import struct

# client
START_CRACK = 0
TAKE_MORE = 1
DONE = 2
SUCCESS = 3

# server
GIVE_GENOME = 0
GIVE_MORE = 1
NO_MORE = 2


def start_crack(my_uuid):
    return struct.pack("!bi16ss", START_CRACK, 0, my_uuid, "".encode("utf8"))

def take_more(my_uuid):
    return struct.pack("!bi16ss", TAKE_MORE, 0, my_uuid, "".encode("utf8"))

def done(seq: (str, int), my_uuid):
    return struct.pack("!bi16si{}s".format(len(seq[0])), DONE, seq[1], my_uuid, len(seq[0]), seq[0].encode("utf8"))

def success(genome: str, my_uuid):
    return struct.pack("!bi16s{}s".format(len(genome.encode("utf8"))), SUCCESS, len(genome), my_uuid, genome.encode("utf8"))

def give_genome(encrypted_genome: bytes):
    return struct.pack("!bi{}s".format(len(encrypted_genome)), GIVE_GENOME, len(encrypted_genome), encrypted_genome)

def give_more(seq: (str, int)):
    return struct.pack("!bii{}s".format(len(seq[0])), GIVE_GENOME, seq[1], len(seq[0]), seq[0].encode("utf8"))

def no_more():
    return struct.pack("!bis", NO_MORE, 0, "".encode("utf8"))

def read(msg):
    return struct.unpack("!bis", msg)

def parse_msg_type(data: bytes):
    return struct.unpack("!b", data[:1])[0]

def parse_genome(data: bytes):
    genome_len = struct.unpack("!i", data[1:5])[0]
    return struct.unpack("!{}s".format(genome_len), data[5:])[0]

def parse_uuid(data: bytes):
    uuid = struct.unpack("!16s", data[5:21])
    return uuid

def parse_more_cli(data: bytes):
    steps = struct.unpack("!i", data[1:5])[0]
    seq_len = struct.unpack("!i", data[5:9])[0]
    seq = struct.unpack("!{}s".format(seq_len), data[9:])[0].decode("utf8")
    return steps, seq

def parse_more_serv(data: bytes):
    steps = struct.unpack("!i", data[1:5])[0]
    seq_len = struct.unpack("!i", data[21:25])[0]
    seq = struct.unpack("!{}s".format(seq_len), data[25:])[0].decode("utf8")
    return steps, seq

def parse_success(data: bytes):
    genome_len = struct.unpack("!i", data[1:5])[0]
    seq = struct.unpack("!{}s".format(genome_len), data[21:])[0].decode("utf8")
    return seq