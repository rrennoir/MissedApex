import win32api

from PyOverlay import *
from SharedMemory.PyAccSharedMemory import *
from keycode import KeyCode

from pygame import mixer


def string_time_from_ms(time_in_ms: int) -> str:

    minute = time_in_ms // 60_000
    second = (time_in_ms % 60_000) // 1000
    millisecond = (time_in_ms % 60_000) % 1000

    if minute < 10:
        minute_str = f"0{minute}"

    else:
        minute_str = str(minute)

    if second < 10:
        second_str = f"0{second}"

    else:
        second_str = str(second)

    if millisecond < 100:
        millisecond_str = f"0{millisecond}"

    elif millisecond < 10:
        millisecond_str = f"00{millisecond}"

    else:
        millisecond_str = str(millisecond)

    return f"{minute_str}:{second_str}.{millisecond_str}"


def is_key_pressed(key: KeyCode) -> bool:
    # is pressed is the & 0x8000 part
    return bool(win32api.GetAsyncKeyState(key.value) & 0x8000)


class MissedApex(Overlay):

    def __init__(self, window_name: str, refresh_rate: int) -> None:
        super().__init__(window_name, refresh_rate)

        mixer.init()
        self.sound = mixer.Sound("beep.wav")
        # self.sound = mixer.Sound("./yamete-kudasai.wav") # need to get stuck in the limiter for 3s though
        self.sound.set_volume(0.15)
        self.channel = mixer.Channel(0)

        self.create_rev_light(10, 200, 10)


    def create_rev_light(self, x:int, y:int, segments: int) -> None:

        Xoffset = 10
        Xsize = 50
        Ysize = 10
        current_offset = 0

        self.segment_pos = []
        self.segment_count = segments
        self.segment_color = [(4, Color.GREEN), (2, Color.YELLOW), (2, Color.ORANGE), (2, Color.RED)]
        for i in range(self.segment_count):
            self.segment_pos.append(Vector(x + current_offset, y, Xsize, Ysize))
            current_offset += Xsize + Xoffset


    def draw_rev_light(self, rpm: int) -> None:
        heighest_rpm = 7500
        lowest_rpm = 6000
        rpm_step = (heighest_rpm - lowest_rpm) // self.segment_count
        rpm_segment = [i for i in range(6000 + rpm_step, 7500 + 1, rpm_step)]

        for index, segment in enumerate(self.segment_pos):
            
            if rpm > rpm_segment[index]:
                color = Color.GREEN
            
            else:
                color = Color.RED

            self.draw("fillRect", segment, color.value)


    def beep(self) -> None:
        if not self.channel.get_busy():
            self.channel.play(self.sound)


    def stop_sound(self) -> None:
        self.channel.stop()


def main():

    asm = accSharedMemory()
    if not asm.start():
        print("Fucked up")

    app = MissedApex("AC2", 60)
    font = app.CreateFont("Fixedsys", 100)

    while not(is_key_pressed(KeyCode.CTRL_L) and is_key_pressed(KeyCode.NUM_0)):
        OnUpdate(asm, app, font)

    asm.stop()


def OnUpdate(asm: accSharedMemory, overlay: MissedApex, font):

    borderVec = Vector(0, 0, 1280, 720)
    queueVec = Vector(10, 100, 200, 50)

    sm = asm.get_sm_data()

    if sm and sm["physics"] and sm["graphics"]:

        if overlay.IsTargetFocused() and sm["graphics"]["acc_status"] == ACC_STATUS.ACC_LIVE:

            rpm = sm["physics"]["rpm"]
            gas = sm["physics"]["gas"]


            overlay.draw("BorderRect", vector=borderVec, color=Color.RED.value)
            overlay.draw("Text", queueVec, Color.BLUE.value,
                            text=f"Queue: {asm.get_queue_size()} items", fontObject=font)

            overlay.draw_rev_light(rpm)

            if rpm >= 7500 and gas == 1.0:
                overlay.beep()
            
            elif (rpm <= 7000):
                overlay.stop_sound()
           

    overlay.handle()


if __name__ == "__main__":
    main()

    