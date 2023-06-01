import pygame as pg
import pygame_gui
from pyo import *

class Cardioid:
    def __init__(self, app):
        self.app = app
        self.radius = 600
        self.num_lines = self.app.frequency * 5
        self.angle_offset = 0
        self.colors = ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta']  

    def update(self):
        sound_value = self.app.get_sound_value() 
        frequency = self.app.frequency  

      
        x_offset = frequency * 0.12 
        y_offset = frequency * 0.12  

        self.x_offset = x_offset
        self.y_offset = y_offset

    def draw(self):
        for i in range(self.num_lines):
            theta = math.radians((360 / self.num_lines) * i)
            x1 = (self.radius * 0.05 * self.x_offset) / 4 * math.cos(theta * self.app.frequency * 0.002) + self.app.screen_width // 2
            y1 = (self.radius / 4) * math.sin(theta * 2 * self.app.get_envelope_value()) + self.app.screen_height // 2
            x2 = self.radius / 4 * math.cos(7.5 * theta * self.app.get_envelope_value() + self.angle_offset) + self.app.screen_width // 2
            y2 = (self.radius * 0.02 * self.y_offset) / 4 * math.sin(3.6 * theta * self.app.modulator_freq * 0.002 + self.angle_offset) + self.app.screen_height // 2

            color1 = 'purple'
            color2 = 'black'  # Get the current color based on index
            pg.draw.aaline(self.app.screen, color1, (x1, y1), (x2, y2))


            self.angle_offset += 0.000007 * (self.app.frequency / 6)  # Adjust the animation speed by changing the increment value

class App:
    def __init__(self):
        self.frequency = 100  
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pg.display.set_mode([self.screen_width, self.screen_height])
        self.clock = pg.time.Clock()
        self.cardioid = Cardioid(self)
        self.current_color_index = 0 

        # Initialize Pyo audio server
        self.server = Server(audio='portaudio', duplex=0, nchnls=2).boot()
        self.server.start()
        self.release_time = 0.1 
        self.release_frames = int(self.release_time * self.server.getSamplingRate())


        self.key_notes = ['z', 's', 'x', 'd', 'c', 'v', 'g', 'b', 'h', 'n', 'j', 'm', 'q', '2', 'w', '3', 'e', 'r', '5', 't', '6', 'y', '7', 'u', 'i', '9', 'o', '0', 'p', '[', '=', ']', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", '\\', '`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/']
        self.key_pressed = set()
        modfrequency = self.frequency * 10


        self.env = Adsr(attack=0.5, decay=0.8, sustain=0, release=0.8)

        # Create FM synthesis objects
        self.carrier = Sine(freq=self.frequency, mul=self.env)
        self.modulator_freq = modfrequency
        self.modulator = Sine(freq=self.modulator_freq, mul=1000 * self.env)
        self.fm = FM(carrier=self.carrier, ratio=self.modulator, mul=self.env / 2)

        self.out = self.fm.mix(2).out()

    
        self.gui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height))

  
        slider_rect = pg.Rect(50, 50, 200, 20)
        self.frequency_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=slider_rect,
            start_value=self.frequency,
            value_range=(50, 1000),
            manager=self.gui_manager
        )

    def get_envelope_value(self):
        return self.env.get()

    def get_sound_value(self):
        return self.carrier.get()

    def set_frequency(self, value):
        self.frequency = value
        self.carrier.setFreq(value)
        self.modulator_freq = value * 1
        self.modulator.setFreq(self.modulator_freq * 2)

    def get_note_frequency(self, note_index):
        reference_frequency = 440.0  # A4 reference frequency in Hz
        semitone_ratio = 2 ** (1 / 12)  # Ratio between consecutive semitones
        return reference_frequency * (semitone_ratio ** (note_index - 21))

    def play_notes(self):
        for note_index in self.key_pressed:
            frequency = self.get_note_frequency(note_index)
            self.set_frequency(frequency)
            self.env.play() 
            self.fm.play() 

       
        if not self.key_pressed:
            release_frames = int(self.release_time * self.server.getSamplingRate())
            self.env.release = self.release_time
            self.release_frames = release_frames

        # Stop the envelope and FM synthesis when release is complete
        if self.release_frames > 0:
            self.release_frames -= 1
        elif not self.key_pressed:
            self.env.stop()
            self.fm.stop()


    def stop_notes(self):
        for note_index in self.key_pressed:
            self.env.stop()  
            self.fm.stop()  

    def draw(self):
        self.screen.fill('white')
        self.cardioid.update()  
        self.cardioid.draw()

    
        self.gui_manager.update(self.clock.tick(60) / 1000.0)
        self.gui_manager.draw_ui(self.screen)

        pg.display.flip()

    def handle_key_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key in range(pg.K_a, pg.K_z + 1):
                note_index = self.key_notes.index(chr(event.key).lower())
                self.key_pressed.add(note_index)

                
                self.current_color_index = (self.current_color_index + 1) % len(self.cardioid.colors)

        if event.type == pg.KEYUP:
            if event.key in range(pg.K_a, pg.K_z + 1):
                note_index = self.key_notes.index(chr(event.key).lower())
                self.key_pressed.discard(note_index)

                if not self.key_pressed:
                    
                    self.release_frames = int(self.release_time * self.server.getSamplingRate())


    def handle_slider_event(self, event):
        if event.type == pg.USEREVENT:
            if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == self.frequency_slider:
                    self.set_frequency(event.value)

    def run(self):
        running = True

        while running:
            self.cardioid.update()
            self.play_notes()
            self.draw()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type in (pg.KEYDOWN, pg.KEYUP):
                    self.handle_key_event(event)

         
                self.gui_manager.process_events(event)
                self.handle_slider_event(event)

            self.gui_manager.update(self.clock.tick(60) / 1000.0)


        self.env.stop()
        self.server.stop()

if __name__ == '__main__':
    pg.init()
    app = App()
    app.run()
    pg.quit() 

