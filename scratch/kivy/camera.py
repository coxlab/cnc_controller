from kivy.app import App
from kivy.uix.camera import Camera
from kivy.uix.widget import Widget


class CameraApp(App):
    def build(self):
        root = Widget()
        camera = Camera(resolution=(640, 480), play=True)

        root.add_widget(camera)
        return root

CameraApp().run()
