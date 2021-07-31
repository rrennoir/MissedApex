import win32api
import json
import os

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
        self.sound = mixer.Sound("Sounds/beep.wav")
        # self.sound = mixer.Sound("Sounds/yamete-kudasai.wav") # need to get stuck in the limiter for 3s though
        self.sound.set_volume(0.15)
        self.channel = mixer.Channel(0)

        self.segment_pos = []
        self.segment_count = 10
        self.segment_color = [(4, Color.GREEN), (2, Color.YELLOW), (2, Color.ORANGE), (2, Color.RED)]
        self.segment_color_table = self.create_segment_color_table()

        self.cars_infos = self.load_cars_infos()
        self.create_rev_light(10, 200)
        self._current_carID = -1

    @property
    def current_carID(self):
        return self._current_carID

    @current_carID.setter
    def current_carID(self, carID):
        self._current_carID = carID

        heighest_rpm = self.cars_infos[carID]["rpm_shift_range"]
        lowest_rpm = self.cars_infos[carID]["lowest_rpm_segment"]
        rpm_step = (heighest_rpm - lowest_rpm) // self.segment_count

        if len(self.cars_infos[carID]["segment_rpm"]) == self.segment_count:
            self.rpm_segment = self.cars_infos[carID]["segment_rpm"]
        
        else:
            print("[MissedApex] 'segment_rpm' not set or invalide, using auto generated one.")
            self.rpm_segment = [i for i in range(lowest_rpm, heighest_rpm, rpm_step)]

    def load_cars_infos(self) -> dict:
        files = os.listdir("Cars")

        cars_infos = {}
        for file in files:
            if file.endswith(".json"):
                with open(f"Cars/{file}", "r") as fp:
                    infos = json.load(fp)
                    cars_infos[infos["carID"]] = infos

        return cars_infos

    def create_rev_light(self, x: int, y: int) -> None:

        Xoffset = 10
        Xsize = 50
        Ysize = 10
        current_offset = 0

        for _ in range(self.segment_count):
            self.segment_pos.append(Vector(x + current_offset, y, Xsize, Ysize))
            current_offset += Xsize + Xoffset

    def create_segment_color_table(self) -> list:

        segment_color_table = []
        for i in self.segment_color:
            for _ in range(i[0]):
                segment_color_table.append(i[1])

        return segment_color_table

    def draw_rev_light(self, rpm: int) -> None:

        if self.cars_infos[self.current_carID]["rpm_shift_range"] <= rpm:
            for segment in self.segment_pos:
                self.draw("fillRect", segment, Color.BLUE.value)

        else:
            for index, segment in enumerate(self.segment_pos):
                
                if rpm > self.rpm_segment[index]:
                    color = self.segment_color_table[index]
                
                else:
                    color = Color.BLACK

                self.draw("fillRect", segment, color.value)

    def beep(self) -> None:
        if not self.channel.get_busy():
            self.channel.play(self.sound)

    def stop_sound(self) -> None:
        self.channel.stop()

    @staticmethod
    def name_to_id(car_name: str) -> int:

        name_ids = {
            "porsche_991_gt3_r": 0,
            "mercedes_amg_gt3": 1,
            "ferrari_488_gt3": 2,
            "audi_r8_lms": 3,
            "lamborghini_huracan_gt3": 4,
            "mclaren_650s_gt3": 5,
            "nissan_gt_r_gt3_2018": 6,
            "bmw_m6_gt3": 7,
            "bentley_continental_gt3_2018": 8,
            "porsche_991ii_gt3_cup": 9,
            "nissan_gt_r_gt3_2017": 10,
            "bentley_continental_gt3_2016": 11,
            "amr_v12_vantage_gt3": 12,
            "lamborghini_gallardo_rex": 13,
            "jaguar_g3": 14,
            "lexus_rc_f_gt3": 15,
            "lamborghini_huracan_gt3_evo": 16,
            "honda_nsx_gt3": 17,
            "lamborghini_huracan_st": 18,
            "audi_r8_lms_evo": 19,
            "amr_v8_vantage_gt3": 20,
            "honda_nsx_gt3_evo": 21,
            "mclaren_720s_gt3": 22,
            "porsche_991ii_gt3_r": 23,
            "ferrari_488_gt3_evo": 24,
            "mercedes_amg_gt3_evo": 25,
            "alpine_a110_gt4": 50,
            "amr_v8_vantage_gt4": 51,
            "audi_r8_gt4": 52,
            "bmw_m4_gt4": 53,
            "chevrolet_camaro_gt4r": 55,
            "ginetta_g55_gt4": 56,
            "ktm_xbow_gt4": 57,
            "maserati_mc_gt4": 58,
            "mclaren_570s_gt4": 59,
            "mercedes_amg_gt4": 60,
            "porsche_718_cayman_gt4_mr": 61
        }

        for name in name_ids.keys():
            if car_name.startswith(name):
                return name_ids[name]


def main():

    asm = accSharedMemory()
    if not asm.start():
        print("Fucked up")

    app = MissedApex("AC2", 60)
    font = app.CreateFont("Fixedsys", 100)

    # CTRL + 0 (numpad) to close
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
            carID = overlay.name_to_id(sm["statics"]["carModel"])

            if carID != overlay.current_carID:
                overlay.current_carID = carID

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

    