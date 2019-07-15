#!/usr/local/bin/python3
# encodin: utf-8
# author: cx

"""
经过测试 cv2.VideoCapture 的 read 函数并不能获取实时流的最新帧
而是按照内部缓冲区中顺序逐帧的读取，opencv会每过一段时间清空一次缓冲区
但是清空的时机并不是我们能够控制的，因此如果对视频帧的处理速度如果跟不上接受速度
那么每过一段时间，在播放时(imshow)时会看到画面突然花屏，甚至程序直接崩溃

在网上查了很多资料，处理方式基本是一个思想
使用一个临时缓存，可以是一个变量保存最新一帧，也可以是一个队列保存一些帧
然后开启一个线程读取最新帧保存到缓存里，用户读取的时候只返回最新的一帧
这里我是使用了一个变量保存最新帧

注意：这个处理方式只是防止处理（解码、计算或播放）速度跟不上输入速度
而导致程序崩溃或者后续视频画面花屏，在读取时还是丢弃一些视频帧
"""

import sys
import threading
import cv2



class RTSCapture(cv2.VideoCapture):
    """
        Real Time Streaming Capture

        这个类必须使用 RTSCapture.create 方法创建，请不要直接实例化
    """
    @staticmethod
    def create(url, maxsize=10):
        rtscap = RTSCapture(url)
        rtscap.__cur_frame__ = None
        rtscap.frame_receiver = threading.Thread(target=rtscap.put_frame, daemon=True)
        return rtscap

    def isStarted(self):
        ret = self.isOpened()
        if ret:
            ret = self.frame_receiver.is_alive()

        return ret

    def put_frame(self):
        while self.isOpened():
            ok, frame = self.read()
            if not ok:
                break
            self.__cur_frame__ = frame

    def read_frame(self):
        frame = self.__cur_frame__
        ret = frame is not None
        self.__cur_frame__ = None
        return ret, frame

    def start_read(self):
        self.frame_receiver.start()

if __name__ == '__main__':
    rtscap = RTSCapture.create(sys.argv[1])
    rtscap.start_read()
    
    while rtscap.isStarted():
        ok, frame = rtscap.read_frame()
        if not ok:
            if cv2.waitKey(100) & 0xFF == ord('q'): break
            continue

        cv2.imshow("cam", frame)

        if cv2.waitKey(100) & 0xFF == ord('q'):
            break

    rtscap.release()
    cv2.destroyAllWindows()
