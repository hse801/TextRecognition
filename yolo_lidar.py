import cv2
import numpy as np
import serial
from math import atan, pi, floor
import matplotlib.pyplot as plt
import math
from aws_tts import tts
import time

anglecheck1 = []
anglecheck2 = []
ddict = []
dist = []
angle = []


def startyolo():
    global num1

    # while True:

    global anglecheck1
    global anglecheck2

    num1 = 0
    num2 = 0
    num3 = 0

    obj1_yolo_angle = np.array([[0.0 for col in range(50)] for row in range(50)])
    obj2_yolo_angle = np.array([[0.0 for col in range(50)] for row in range(50)])

    obj_exist = []
    obj1_exist = 0
    obj2_exist = 0

    start = time.time()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(3, 1920)
    cap.set(4, 1080)
    ret, image = cap.read()
    cv2.imwrite("C:/Users/user/1.jpg", image)
    cap.release()
    img = cv2.imread("C:/Users/user/1.jpg")
    print("time :", time.time() - start)

    # Yolo 로드
    net = cv2.dnn.readNet("C:/Users/user/yolov3.weights", "C:/Users/user/yolov3.cfg")
    classes = []
    with open("C:/Users/user/coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))

    # img = cv2.resize(img, None, fx=0.4, fy=0.4)
    height, width, channels = img.shape

    # Detecting objects

    blob = cv2.dnn.blobFromImage(image, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # 정보를 화면에 표시
    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                # Object detected
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)

                print("center_x =",center_x)

                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # 좌표

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

                # 노이즈 제거
                indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

                # num1이 사진의 개수, num2가 마지막 사진에서 label이 person인 bounding box 개수
                # num3는 마지막 사진에서 label이 bottle인 bounding box 개수
                # 배열에 나머지 값은 0이고 조건에 해당될때만 anglecheck 값을 할당
                # 배열을 장애물 별로 따로 저장하여 라이다로 넘긴다
                # num1 - 1 번째 행만 가져와야함

                font = cv2.FONT_HERSHEY_PLAIN
                for i in range(len(boxes)):
                    if i in indexes:
                        x, y, w, h = boxes[i]

                        # x가 bounding box의 시작 좌표
                        # w가 box의 길이
                        label = str(classes[class_ids[i]])
                        color = colors[i]
                        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(img, label, (x, y + 30), font, 3, color, 3)

                        if label == "person":
                            # global obj1_yolo_angle
                            # global num2
                            # global obj1_exist

                            if (x + w / 2) <= 960:
                                obj1_yolo_angle[num1, num2] = 35 - math.degrees(atan((960 - (x + w / 2)) / 1371))
                                # atan의 결과로 나온 라디안 값은 degree로 변환
                            else:
                                obj1_yolo_angle[num1, num2] = 35 + math.degrees(atan((x + w / 2) / 1371))
                            num2 += 1
                            obj1_exist = 1
                        if label == "chair":
                            # global obj2_yolo_angle
                            # global num3
                            # global obj2_exist
                            if (x + w / 2) <= 960:
                                obj2_yolo_angle[num1, num3] = 35 - math.degrees(atan((960 - (x + w / 2)) / 1371))
                            else:
                                obj2_yolo_angle[num1, num3] = 35 + math.degrees(atan((x + w / 2) / 1371))
                            num3 += 1
                            obj2_exist = 1
                cv2.imshow("Image", img)
                cv2.waitKey(1000)
                cv2.destroyAllWindows()
                num1 += 1

    anglecheck_obj1 = obj1_yolo_angle[num1 - 1, :]
    anglecheck_obj2 = obj2_yolo_angle[num1 - 1, :]

    anglecheck1 = anglecheck_obj1[anglecheck_obj1 > 0]
    anglecheck2 = anglecheck_obj2[anglecheck_obj2 > 0]

    print("anglecheck1 = ", anglecheck1)
    print("anglecheck2 = ", anglecheck2)

    obj_exist.append(obj1_exist)
    obj_exist.append(obj2_exist)

    return obj_exist


def read_Lidar():

    # dist = []
    # angle = []
    print('after dist = ', dist)

    def plot_lidar(distdict):

        x = [0 for i in range(360)]
        y = [0 for i in range(360)]

        for angle in range(0, 360):
            x[angle] = distdict[angle] * math.cos(math.radians(angle))
            y[angle] = distdict[angle] * math.sin(math.radians(angle))

        # plt.figure(1)
        # plt.cla()
        # plt.ylim(-3000, 3000)
        # plt.xlim(-3000, 3000)
        # plt.scatter(x, y, c='r', s=8)
        # plt.pause(0.001)

    def _CheckSum(data):

        try:
            ocs = _HexArrToDec((data[6], data[7]))
            LSN = data[1]
            cs = 0x55AA ^ _HexArrToDec((data[0], data[1])) ^ _HexArrToDec((data[2], data[3])) ^ _HexArrToDec(
                (data[4], data[5]))

            for i in range(0, 2 * LSN, 2):
                cs = cs ^ _HexArrToDec((data[8 + i], data[8 + i + 1]))
            if cs == ocs:
                return True
            else:
                return False
        except Exception as e:
            return False

    def _HexArrToDec(data):

        littleEndianVal = 0

        for i in range(0, len(data)):
            littleEndianVal = littleEndianVal + (data[i] * (256 ** i))
        return littleEndianVal

    def _AngleCorr(dist):

        if dist == 0:
            return 0
        else:
            return atan(21.8 * ((155.3 - dist) / (155.3 * dist))) * (180 / pi)

    def _Calculate(d):

        # global dist_sum

        global dist
        global angle
        global ddict
        

        LSN = d[1]
        Angle_fsa = ((_HexArrToDec((d[2], d[3])) >> 1) / 64.0)
        Angle_lsa = ((_HexArrToDec((d[4], d[5])) >> 1) / 64.0)

        if Angle_fsa < Angle_lsa:
            Angle_diff = Angle_lsa - Angle_fsa
        else:
            Angle_diff = 360 + Angle_lsa - Angle_fsa

        for i in range(0, 2 * LSN, 2):
            global dist_i
            dist_i = _HexArrToDec((d[8 + i], d[8 + i + 1])) / 4
            # dist_i = 2
            Angle_i_tmp = ((Angle_diff / float(LSN)) * (i / 2)) + Angle_fsa
            if Angle_i_tmp > 360:
                Angle_i = Angle_i_tmp - 360
            elif Angle_i_tmp < 0:
                Angle_i = Angle_i_tmp + 360
            else:
                Angle_i = Angle_i_tmp
            Angle_i = Angle_i + _AngleCorr(dist_i)
            ddict.append((dist_i, Angle_i))
            dist.append(dist_i * 2)
            angle.append(Angle_i)
            return ddict
        print('before dist = ', dist)

    def _Mean(data):

        length_of_data_without_zero = sum([i != 0 for i in data])
        if len(data) > 0 and length_of_data_without_zero != 0:
            #        return int(sum(data)/len(data)) # original By ydlidar
            return float(sum(data) / length_of_data_without_zero)  # modified for remove zero value
        return 0

    def code(ser):

        data1 = ser.read(6000)
        data2 = data1.split(b"\xaa\x55")[1:-1]
        distdict = {}

        for i in range(0, 360):
            distdict.update({i: []})

        for i, e in enumerate(data2):
            try:
                if e[0] == 0:
                    if _CheckSum(e):
                        d = _Calculate(e)
                        for ele in d:
                            angle = floor(ele[1])
                            if 0 <= angle < 360:
                                distdict[angle].append(ele[0])
            except Exception as e:
                pass

        for i in distdict.keys():
            distdict[i] = _Mean(distdict[i])

        yield distdict

    def main():
        # Open Serial
        ser = serial.Serial(port='COM13', baudrate=512000)
        ser.isOpen()

        # Scan start
        values = bytearray([int('a5', 16), int('60', 16)])
        ser.write(values)

        for i in range(10):

            angle_data = code(ser)
            plot_lidar(next(angle_data))

        # # Scan End
        # values = bytearray([int('a5', 16), int('65', 16)])
        # ser.write(values)
        #
        # # Close Serial
        # ser.close()

    if __name__ == '__main__':
        main()


def obstacle():
    # while True:
    # finaldist랑 finalangle 왜 초기화 안될까...

    exist = startyolo()
    read_Lidar()

    finaldist = dist  # distance와 angle 새로운 변수에 저장
    finalangle = angle

    print("finaldist = ", finaldist)
    print('finalangle =', finalangle)

    anglecheckdone1 = []
    anglecheckdone2 = []
    distcheckdone1 = []
    distcheckdone2 = []
    nonzero_DCD1 = []
    nonzero_DCD2 = []
    sumDCD1 = []  # 리스트(1개의 행)
    sumDCD2 = []
    avgdist1 = 0
    avgdist2 = 0
    # finaldist = []
    # finalangle = [] #add

    # round_dist1 = 0
    # round_dist2 = 0

    # person
    if exist[0] == 1:
        for k in range(len(anglecheck1)):

            # https://dojang.io/mod/page/view.php?id=2291

            anglecheckdone1.append([])
            distcheckdone1.append([])
            nonzero_DCD1.append([])

            for j in range(len(finalangle)):
                if 0 <= finalangle[j] <= 500:
                    # if (finalangle[j] - 5 <= anglecheck1[k] + 149 <= finalangle[j] + 5) and (134 <= finalangle[j] <= 244):
                    anglecheckdone1[k].append(finalangle[j])
                    distcheckdone1[k].append(finaldist[j])
                else:
                    anglecheckdone1[k].append(0)
                    distcheckdone1[k].append(0)
            nonzero_DCD1[k] = [float(v) for v in distcheckdone1[k] if v > 0]
            sumDCD1.append(sum(nonzero_DCD1[k]))

        print("distcheckdone1 = ", distcheckdone1)
        print("nonzero_DCD1 = ", nonzero_DCD1)
        print("sumDCD1 = ", sumDCD1)

        if sumDCD1 != []:
            if len(nonzero_DCD1[sumDCD1.index(min(sumDCD1))]) != 0:
                avgdist1 = min(sumDCD1) / len(nonzero_DCD1[sumDCD1.index(min(sumDCD1))])
                # round_dist1 = round(avgdist1 / 1000)
                print('nonzero_DCD1[sumDCD1.index(min(sumDCD1))] = ',nonzero_DCD1[sumDCD1.index(min(sumDCD1))])
        print('avgdist1 = ', avgdist1)
    # bottle

    if exist[1] == 1:
        for k in range(len(anglecheck2)):
            # https://dojang.io/mod/page/view.php?id=2291
            anglecheckdone2.append([])
            distcheckdone2.append([])
            nonzero_DCD2.append([])

            for j in range(len(finalangle)):
                if (finalangle[j] - 5 <= anglecheck2[k] + 149 <= finalangle[j] + 5) and (134 <= finalangle[j] <= 234):
                    anglecheckdone2[k].append(finalangle[j])
                    distcheckdone2[k].append(finaldist[j])
                else:
                    anglecheckdone2[k].append(0)
                    distcheckdone2[k].append(0)

            nonzero_DCD2[k] = [float(v) for v in distcheckdone2[k] if v > 0]
            sumDCD2.append(sum(nonzero_DCD2[k]))

        print("distcheckdone2 = ", distcheckdone2)
        print("nonzero_DCD2 = ", nonzero_DCD2)
        print("sumDCD2 = ", sumDCD2)

        if sumDCD2 != []:
            if len(nonzero_DCD2[sumDCD2.index(min(sumDCD2))]) != 0:
                avgdist2 = min(sumDCD2) / len(nonzero_DCD2[sumDCD2.index(min(sumDCD2))])
                # round_dist2 = round(avgdist2 / 1000)
                print('nonzero_DCD2[sumDCD2.index(min(sumDCD2))] = ', nonzero_DCD2[sumDCD2.index(min(sumDCD2))])

        print('avgdist1 = ', avgdist1)
        print('avgdist2 = ', avgdist2)

    if exist[0] == 1 and exist[1] == 1: # 서로 다른 2가지 장애물 잡힐 경우 더 가까운 것만 안내
        if avgdist1 > avgdist2:
            avgdist1 = 0
        else:
            avgdist2 = 0

    round_dist1 = round(avgdist1 / 1000)
    round_dist2 = round(avgdist2 / 1000)

    # 최종결과

    if round_dist1 != 0:
        if exist[0] == 1:
            if round_dist1 < 1:
                print("1미터 내 사람.")
                text1 = "1미터 내 사람."
                tts(text1)
            else:
                print(round_dist1, "미터 앞 사람.")
                text1 = str(round_dist1) + "미터 앞 사람."
                tts(text1)
    if round_dist2 != 0:
        if exist[1] == 1:
            if round_dist2 < 1:
                print("1미터 내 의자.")
                text2 = "1미터 내 의자."
                tts(text2)
            else:
                print(round_dist2, "미터 앞 의자.")
                text2 = str(round_dist2) + "미터 앞 의자."
                tts(text2)

def lidar_end():

    ser = serial.Serial(port='COM13', baudrate=512000)

    # Scan End
    values = bytearray([int('a5', 16), int('65', 16)])
    ser.write(values)

    # Close Serial
    ser.close()


def main():
    menu = int(input("입력하세요!(시작 : 1, 끝 : 2) : "))

    if menu == 1:
        while True:
            obstacle()
    elif menu == 2:
        lidar_end()
    else:
        while menu != 1 and menu != 2:
            menu = int(input("다시 누르세요! (시작 : 1, 끝 : 2) : "))
        if menu == 1:
            while True:
                obstacle()
        elif menu == 2:
            lidar_end()

main()
