import argparse
from hashlib import md5
import socket
import proto
import signal
import sys
from uuid import uuid4 
from time import sleep

my_uuid = None
sock = None 

def exit_handler(arg1, arg2):
    print()
    print("Good Bye!")
    if sock:
        sock.close()
    sys.exit(0)

def cracked(candidate: str, encrypted_genome: str) -> bool:
    return md5(candidate.encode("utf8")).digest() == encrypted_genome

def get_next_seq(seq: str, pos) -> str:
    if pos > len(seq):
        return seq
    if seq[-pos] == "a":
        return seq[:-pos] + "c" + "a" * (pos - 1)
    elif seq[-pos] == "c":
        return seq[:-pos] + "g" + "a" * (pos - 1)
    elif seq[-pos] == "g":
        return seq[:-pos] + "t" + "a" * (pos - 1)
    elif seq[-pos] == "t":
        return get_next_seq(seq, pos + 1)

def create_ranges():

    sequences = []

    prefix_len = math.ceil(MAX_LEN / 2 - 1)
    postfix_len = MAX_LEN - prefix_len
    amm_of_ranges = 4 ** prefix_len
    num_of_steps_in_range = 4 ** postfix_len

    def generate(seq, len):
        sequences.append(("",num_of_steps_in_range))
        for c in acgt:
            sequences.append((seq + c + 'a' * postfix_len, num_of_steps_in_range))
            if(len > 1):
                generate(seq + c, len - 1)
    generate("", prefix_len)
    return sequences

def crack(seq: str, count: int, encrypted_genome: str) -> (str, bool):
    print("Cracking from '{0}' for {1} steps.".format(seq,count))

    if seq == "":
        length = 1
        while count != 1:
            length += 1
            count /= 4
        sequences = []
        acgt = ["a", "c", "g", "t"]

        def generate(seq, len):
            for c in acgt:
                sequences.append(seq + c)
                if (len > 1):
                    generate(seq + c, len - 1)
        generate("", length)
        for seq in sequences:
            if cracked(seq,encrypted_genome):
                return seq, True
        else:
            return "", False
    
    for i in range(count):
        if not cracked(seq, encrypted_genome):
            seq = get_next_seq(seq, 1)
        else:
            return seq, True
    else:
        return "", False


def try_crack(data: bytes, genome: str) -> (str, bool):
    if proto.parse_msg_type(data) == proto.NO_MORE:
        print("No more work. Bye!")
        sys.exit(0)
    steps, seq = proto.parse_more_cli(data)
    return crack(seq, steps, genome)


def send_msg(server, port, msg: bytes):
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server, port))
    except:
        print("Can't connect. Retrying after 1 seccond")
        sleep(1)
        return send_msg(server,port, msg)
    sock.send(msg)
    response = sock.recv(1024)
    sock.close()
    return response


def main(server: str, port: int):
    signal.signal(signal.SIGINT, exit_handler)
    my_uuid = uuid4().bytes
    data = send_msg(server, port, proto.start_crack(my_uuid))
    msg_type = proto.parse_msg_type(data)
    if msg_type == proto.GIVE_GENOME:
        genome = proto.parse_genome(data)
        data = send_msg(server, port, proto.take_more(my_uuid))
        seq, success = try_crack(data, genome)
        while not success:
            steps, seq = proto.parse_more_cli(data)
            send_msg(server, port, proto.done((seq, steps), my_uuid))
            data = send_msg(server, port, proto.take_more(my_uuid))
            seq, success = try_crack(data, genome)
        else:
            send_msg(server, port, proto.success(seq, my_uuid))
            print("I've found correct code! It's '{}'.".format(seq))
    else:
        print("Fail")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Cracks given genome")
    parser.add_argument('server', type=str, help='Server', metavar='Server')
    parser.add_argument('port', type=int, help='Port', metavar='Port')
    args = parser.parse_args()
    main(args.server, args.port)
    sys.exit(0)