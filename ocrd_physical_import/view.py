from itertools import zip_longest

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf
from ocrd_models import OcrdFile
from pkg_resources import resource_filename
from typing import List, Any, Optional
from numpy import array as ndarray

from .scandriver import DummyDriver, AndroidADBDriver, AbstractScanDriver, PageWarpingDriver
from ocrd_browser.util.image import cv_scale, cv_to_pixbuf
from ocrd_browser.view import View


class ViewScan(View):
    """
    Imports book pages from reality
    """

    label = 'Scan'

    def __init__(self, name: str, window: Gtk.Window):
        super().__init__(name, window)
        self.driver = PageWarpingDriver(AndroidADBDriver())
        #self.driver: AbstractScanDriver = DummyDriver('/home/jk/Projekte/archive-tools/projects/exit1/orig/')
        #self.driver: AbstractScanDriver = PageWarpingDriver(DummyDriver('/home/jk/Projekte/archive-tools/projects/exit1/orig/'))
        self.driver.setup()

        self.ui: ScanUi = None
        self.previews: List[GdkPixbuf.Pixbuf] = []
        self.images: List[ndarray] = []

        self.file_group = 'OCR-D-IMG'
        self.template_page_id = 'PAGE_{page_nr:04d}'
        self.template_file_id = '{file_group}_{page_nr:04d}'


    def build(self) -> None:
        super().build()
        self.container.remove(self.scroller)
        self.ui = ScanUi(self, parent=self.container)
        self.previews = [self.ui.preview_left, self.ui.preview_right]
        self.window.actions.create('scan', self.on_scan)
        self.window.actions.create('append', self.on_append)
        self.window.actions.create('insert', self.on_insert)
        self.window.get_application().set_accels_for_action('win.append', ['space'])
        self.window.get_application().set_accels_for_action('win.insert', ['Insert'])
        self.window.get_application().set_accels_for_action('win.scan', ['s'])

    def aquire_images(self):
        return self.driver.scan()

    def on_scan(self, _action: Gio.SimpleAction, _param: Optional[str]) -> None:
        self.images = self.aquire_images()
        self.redraw()

    def on_append(self, _action: Gio.SimpleAction, _param: Optional[str]) -> None:
        # append
        for image in self.images:
            self._add_image(image)

        # and scan next
        self.images = self.aquire_images()
        self.redraw()

    def on_insert(self, _action: Gio.SimpleAction, _param: Optional[str]) -> None:
        page_ids = self.document.page_ids
        inserted_page_ids = []
        for image in self.images:
            inserted_page_ids.append(self._add_image(image).pageId)

        if len(page_ids):
            index = page_ids.index(self.page_id)
            new_page_order = page_ids[:index] + inserted_page_ids + page_ids[index:]
            self.document.reorder(new_page_order)

        self.images = []
        self.update_ui()

    def _add_image(self, image:ndarray) -> OcrdFile:
        page_id, page_nr = self.document.get_unused_page_id(self.template_page_id)
        file_id = self.template_file_id.format(**{'page_nr': page_nr, 'file_group': self.file_group})
        return self.document.add_image(image, page_id, file_id)


    def page_activated(self, _sender: Gtk.Widget, page_id: str) -> None:
        super().page_activated(_sender, page_id)
        self.update_ui()

    def update_ui(self) -> None:
        self.ui.button_scan.set_label('Rescan' if self.images else 'Scan')

        if not self.document.editable:
            self.window.actions['append'].set_enabled(False)
            self.ui.button_append.set_label('Append (Enable Edit Mode first)')
            self.window.actions['insert'].set_enabled(False)
            self.ui.button_insert.set_label('Insert (Enable Edit Mode first)')
            return

        self.ui.button_append.set_label('Append and scan next')
        self.window.actions['append'].set_enabled(self.images)
        if self.document.page_ids:
            self.ui.button_append.set_tooltip_text('Append after #{}'.format(self.document.page_ids[-1]))

        if self.images and self.page_id:
            self.window.actions['insert'].set_enabled(True)
            self.ui.button_insert.set_label('Insert before #{}'.format(self.page_id))
        else:
            self.window.actions['insert'].set_enabled(False)
            self.ui.button_insert.set_label('Insert')


    @property
    def use_file_group(self) -> str:
        return 'OCR-D-IMG'

    def config_changed(self, name: str, value: Any) -> None:
        super().config_changed(name, value)
        self.reload()

    def redraw(self) -> None:
        if self.images:
            preview: Gtk.Image
            for image, preview in zip_longest(self.images, self.previews):
                if image is not None:
                    scaled = cv_scale(image, None, self.ui.preview_height)
                    preview.set_from_pixbuf(cv_to_pixbuf(scaled))
                    preview.set_visible(True)
                else:
                    preview.set_visible(False)
        self.update_ui()


@Gtk.Template(filename=resource_filename(__name__, 'scan.ui'))
class ScanUi(Gtk.Box):
    __gtype_name__ = 'ScanUi'

    button_scan: Gtk.Button = Gtk.Template.Child()
    button_append: Gtk.Button = Gtk.Template.Child()
    button_insert: Gtk.Button = Gtk.Template.Child()

    preview_left: Gtk.Image = Gtk.Template.Child()
    preview_right: Gtk.Image = Gtk.Template.Child()

    def __init__(self, view: ViewScan, **kwargs: Any):
        Gtk.Box.__init__(self, **kwargs)
        self.get_parent().child_set_property(self, 'expand', True)
        self.view: ViewScan = view
        self.preview_height: int = 10

    @Gtk.Template.Callback()
    def on_size_allocate(self, sender: Gtk.Widget, rect: Gdk.Rectangle) -> None:
        if abs(self.preview_height - rect.height) > 4:
            self.preview_height = rect.height
            self.view.redraw()
