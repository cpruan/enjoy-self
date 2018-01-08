import os
import time
import random
from PIL import Image, ImageDraw, ImageFont

def brightness(x,y,img):
    R = img[x,y][0]
    G = img[x,y][1]
    B = img[x,y][2]
    return 3 * R + 6 * G + 1 * B  #Brightness = 0.3 * R + 0.6 * G + 0.1 * B，用整数替代，避免用浮点数降低速度

def aberration(x,y,img):      #色差函数1，用于计算像素与其上方像素的色差值(自定义为RGB三色平方和)，用于确认边缘
    return (img[x,y][0]-img[x,y-1][0])**2 + (img[x,y][1]-img[x,y-1][1])**2 + (img[x,y][2]-img[x,y-1][2])**2

def abercompare(x,y,a,b,img): #色差函数2，用于计算像素与另一像素的色差值，用于确认快速找色块
    return (img[x,y][0]-img[a,b][0])**2 + (img[x,y][1]-img[a,b][1])**2 + (img[x,y][2]-img[a,b][2])**2

def aber(x,y,RGB,img):        #色差函数3，用于计算像素与某一RGB颜色的色差值，用于确认特定颜色（还不熟悉类，多写几个函数将就着...OrZ）
    return (img[x,y][0]-RGB[0])**2 + (img[x,y][1]-RGB[1])**2 + (img[x,y][2]-RGB[2])**2

def search(filename, start, stepy, stepx):   #快速查找函数
    if stepy > 3 and stepx > 3:
        img = Image.open(imgPath + filename).load()
        for y in range(start, resolutiony, stepy): #粗略查找物体位置，默认行间隔50，列间隔5
            for x in range(0, resolutionx, stepx):
                if abercompare(x, y, resolutionx-1, 1280, img) > 400 and y-stepy >= max(resolutiony//4, start):
                    nextstart = y-stepy
                    return search(filename, nextstart, stepy//2, stepx//2)
        return start
    else:
        return start

def timecalculate(filename):  #计算按压时长函数
    image = Image.open(imgPath + filename)
    img = image.load()

    chessman_x = chessman_y = counter_man = 0
    chessboard_x = chessboard_y = counter_board = 0

    start = search(filename, resolutiony//4, 50, 30)
    for y in range(start, resolutiony):
        if counter_man > 0 and y > chessman_y and counter_board > 0 and y > chessboard_y: #一旦棋子和棋盘都找到，则结束循环
            break
        for x in range(resolutionx):
            if counter_man == 0 or y <= chessman_y: #找到棋子后,此行查找完即结束棋子查找
                if 550 > brightness(x, y, img) > 520 and aber(x, y, (52,53,60), img) < 40  and aberration(x, y, img) > 30000: #认为亮度在[520,550)之间,且竖直色差大于50000的，属于棋子的像素（注意：咖啡杯顶部有一个像素亮度刚好为550，故550取闭）
                    if counter_man == 0:
                        chessman_x = x
                        chessman_y = y   #一旦找到第一个位置，chessman_y > 0后，对棋子的搜索即结束
                    counter_man += 1
            if counter_board == 0 or y <= chessboard_y:
                if counter_man > 0:  #但棋子比棋盘先找到时，意味着棋盘离棋子很近，此时寻找棋盘的像素需要消除棋子像素的干扰
                    if brightness(x, y, img) > 600 and aberration(x, y, img) > 1000 and aber(x, y, (52,53,60), img) > 100 and abs(x-chessman_x) > 100: #认为满足亮度大于棋子，色差大于1000的第一个点，属于棋盘的像素
                        if counter_board == 0:
                            chessboard_x = x
                            chessboard_y = y   #一旦找到第一个位置，chessboard_y > 0后，对棋盘的搜索即结束
                        counter_board += 1
                else:
                    if brightness(x, y, img) > 600 and aberration(x, y, img) > 1000:
                        if counter_board == 0:
                            chessboard_x = x
                            chessboard_y = y   #一旦找到第一个位置，chessboard_y > 0后，对棋盘的搜索即结束
                        counter_board += 1

    chessman = chessman_x + counter_man//2
    chessboard = chessboard_x + counter_board//2
    distance = abs(chessboard-chessman)
    time = distance / initdistance * inittime

    # ↓↓↓ 以下为debug模块，需要时开启，输出每次寻找到的棋子、棋盘像素附件区域的图片
    # width, height = 50, 30
    # debugman = Image.new('RGB', (width, height), (255, 255, 255))
    # debugboard = Image.new('RGB', (width, height), (255, 255, 255))
    # debugdrawman = ImageDraw.Draw(debugman)
    # debugdrawboard = ImageDraw.Draw(debugboard)
    # for j in range(height):
    #     for i in range(width):
    #         if i == width//2 and j == height//2:
    #             debugdrawman.point((i, j), fill=(255, 0, 0))
    #             debugdrawboard.point((i, j), fill=(255, 0, 0))
    #         else:
    #             debugdrawman.point((i, j), fill=img[chessman_x - width//2 + i, chessman_y - height//2 + j])
    #             debugdrawboard.point((i, j), fill=img[chessboard_x - width//2 + i, chessboard_y - height//2 + j])
    #
    # font  = ImageFont.truetype(r'C:\Windows\winsxs\amd64_microsoft-windows-font-truetype-arial_31bf3856ad364e35_6.1.7601.19106_none_d0b610f6c3f0f390\arial.ttf', 10)
    # debugdrawman.text((0, 0), 'man', font=font)
    # debugdrawboard.text((0, 0), 'board', font=font)
    # debugnum = int(filename[:-4]) + 1
    # debugman.resize((500, 300)).save(r'c:\Users\Administrator\PycharmProjects\untitled\test\{}-.jpg'.format(debugnum), 'png')
    # debugboard.resize((500, 300)).save(r'c:\Users\Administrator\PycharmProjects\untitled\test\{}--.jpg'.format(debugnum), 'png')
    # ↑↑↑ 以上为debug模块，输出每次寻找的棋子、棋盘区域图像

    image.close()
    return round(time)

def jump_one(filename):
    os.system('adb shell screencap ' + phonePath + filename)                  #第一步，从adb截屏，命名为x.png，存储到phonePath(手机)
    os.system('adb pull ' + phonePath + filename + " " + imgPath + filename)  #第二步，将x.png从phonePath(手机)复制到imgPath(电脑)
    os.system('adb shell rm ' + phonePath + filename)                         #第三步，删除phonePath(手机)上的x.png

    swipetime = timecalculate(filename)                                       #第四步，根据filename调用对应的截图，计算要按压的时间
    os.system('adb shell input swipe 300 1500 300 1500 ' + str(swipetime))    #第五步，根据所算时间执行原位滑动操作

    time.sleep(1)   #需要停顿等图像稳定，另用随机函数防反作弊（不知有用没）
    return swipetime

def main():
    os.system(r'cd c:\Users\Administrator\PycharmProjects\untitled\tools')
    for i in range(1, expected_score+1):
        jumptime = jump_one('{}.png'.format(i))
        print('{}th Jump, Duration = {}ms'.format(i, jumptime))

# ↓↓↓ 以下为初始值设置
expected_score = 70                          #设置预期跳多少步
resolutionx, resolutiony = 1440, 2560        #手机分辨率设置
initdistance = 607                           #游戏初始画面需要跳跃的△x距离,455 for 1080p,607 for 2K
inittime = 723                               #跳跃△x距离需要的按压时间,用于度量，与分辨率无关
phonePath = '/storage/emulated/0/test/'      #安卓手机端截图存储的位置,建议新建一个文件夹
imgPath = r'C:\Users\Administrator\test\\'   #电脑存储图片的位置,建议新建一个文件夹

main()
