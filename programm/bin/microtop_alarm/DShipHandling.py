from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
class BroadCastReceiver:

    msg_len=256

    def __init__(self, port, msg_len=256, timeout=15):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.settimeout(timeout)
        #self.sock.msg_len = msg_len
        self.sock.bind(('', port))

    def __iter__(self):
             return self

    def __next__(self):
             try:
                 addr, data = self.sock.recvfrom(self.msg_len)
                 return addr, data
             except Exception as e:
                 print("Got exception trying to recv %s" % e)
                 raise StopIteration

    def __del__(self):
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()

    def __next__(self):
        try:
            addr, data = self.sock.recvfrom(self.msg_len)
            return addr, data
        except Exception as e:
            print("Got exception trying to recv %s" % e)
            raise StopIteration
        finally:
            self.sock.close()
#-----------------
# main programm


def recieve_data():
    data_dict = {}
    r = BroadCastReceiver(7150, timeout=2)
    data, _ = next(r)
    data = data.decode()
    data = data.splitlines()
    for line in data:
        infos = line.split(",")

        if infos[0] == "$GPZDA":
            data_dict["date"] = infos[4] + infos[3] + infos[2] + infos[1][:6]

        elif infos[0] == "$GPHDT":
            data_dict["heading"] = float(infos[1])

        elif infos[0] == "$GPGGA":
            lat = float(infos[2])/100
            if infos[3] == "S":
                lat *= -1
            data_dict["lat"] = lat

            lon = float(infos[4]) / 100
            if infos[5] == "W":
                lon *= -1
            data_dict["lon"] = lon

    return data_dict


if __name__ == "__main__":
    data = recieve_data()