import socket
import argparse
from hashlib import md5
import math
import proto
from time import time
import signal
import sys

MAX_LEN = 12
POSTFIX_LEN_ = 6
sock = None

def exit_handler(arg1, arg2):
    print()
    print("Good Bye!")
    sock.close()
    sys.exit(0)

def create_ranges():

    sequences = []
    acgt = ["a", "c", "g", "t"]

    prefix_len = math.ceil(MAX_LEN / 2 - 1)
    postfix_len = MAX_LEN - prefix_len
    if postfix_len > POSTFIX_LEN_:
        postfix_len = POSTFIX_LEN_
        prefix_len = MAX_LEN - postfix_len
    amm_of_ranges = 4 ** prefix_len
    num_of_steps_in_range = 4 ** postfix_len
    sequences.append(("",num_of_steps_in_range))

    def generate2(arg):
        sequences_prefs = []
        sequences_prefs.append(('', num_of_steps_in_range))
        for s in sequences_prefs:
            if len(s[0]) < arg:
                for c in acgt:
                        sequences_prefs.append((s[0] + c, num_of_steps_in_range))
        for s in sequences_prefs:
            sequences.append((s[0] + 'a' * postfix_len, s[1]))
#            print(s)
#        for s in sequences:
#            print(s)

    def generate(seq, len):
        for c in acgt:
            sequences.append((seq + c + 'a' * postfix_len, num_of_steps_in_range))
        for c in acgt:
            if(len > 1):
                generate(seq + c, len - 1)
    generate2(prefix_len)
    return sequences

def main(genome, port):
    global sock
    signal.signal(signal.SIGINT, exit_handler)
    print("\nHi! I am {0}\n".format(socket.gethostbyname(socket.gethostname()), port))
    print("Today we are gonna hack genome!\n")
    print("Code to hack: {0}".format(genome))
    encrypted_genome = md5(genome.encode("utf8")).digest()
    print("It's md5    : {0}".format(encrypted_genome))

    print("\nCreating ranges... ",end = "")
    unresolved = create_ranges()
    print("completed!\n")

    in_progress = {}
    resolved = []
    clients = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.listen(1)

    print("Waiting for connections...\n")
    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024)
        uuid = proto.parse_uuid(data)[0]
        clients[uuid] = time()
        msg_type = proto.parse_msg_type(data)

        print("LOG: ", end = "")

        if msg_type == proto.START_CRACK:
            print("New member in our team! Wellcome!")
            conn.send(proto.give_genome(encrypted_genome))

        elif msg_type == proto.TAKE_MORE:
            print("Somebody wants more challenge!", end = "")
            if len(unresolved) > 0:
                for seq in unresolved:
                    conn.send(proto.give_more(seq))
                    print(" Good! Giving prefix '{0}'".format(seq[0]))
                    while seq in unresolved:
                        unresolved.remove(seq)
                    in_progress[seq] = time()

                    break

            elif len(in_progress) > 0:
                max_time = 0
                max_seq = None
                for seq in in_progress:
                    if in_progress[seq] > max_time:
                        max_time = in_progress[seq]
                        max_seq = seq
                conn.send(proto.give_more(max_seq))
                in_progress[seq] = time()

            else:
                print("No more sequenses to crack. Code is wrong.")
                del clients[uuid]
                conn.send(proto.no_more())
                conn.close()
                finish_working(clients)

        elif msg_type == proto.DONE:
            print("Somebody've done work! Excellent!")
            unpacked = proto.parse_more_serv(data)
            seq = (unpacked[0], unpacked[1])
            seq = (seq[1],seq[0])
            del in_progress[seq]
            resolved.append(seq)

        elif msg_type == proto.SUCCESS:
            seq = proto.parse_success(data)
            print()
            print('*' * 34)
            print("* And Finaly we found an answer! *")
            print('*' * 34)
            offset1 = math.ceil((32 - len(seq)) / 2)
            offset2 = 32 - offset1 - len(seq)
            print("{0}{1}{2}".format('*' + ' ' * offset1, seq, offset2 * ' ' + '*'))
            print('*' * 34)
            conn.send(proto.no_more())
            conn.close()
            del clients[uuid]

            finish_working(clients)
        conn.close()

def finish_working(clients):
    sock.settimeout(3)
    print("Finishing work.")
    for cli in clients:
        print(cli)
    try:
        last_time = curr_time = time()
        while len(clients) > 0:
            curr_time = time()
            try:
                conn, addr = sock.accept()
            except:
                sys.exit(0)
            data = conn.recv(1024)
            uuid = proto.parse_success(data)[1]
            conn.send(proto.no_more())
            del clients[uuid]
    except:
        pass

    if len(clients) > 0:
        print("Nobody's answering.")
    else:
        print("No more working clients.")
    sock.close()
    sys.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cracks md5 of given genome")
    parser.add_argument('genome', type=str, help='Genome to crack', metavar='Genome')
    parser.add_argument('port', type=int, help='Port to listen to', metavar='Port')
    args = parser.parse_args()
    main(args.genome, args.port)