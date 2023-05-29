import random


def random_ip(subnet: str) -> str:
    assert "/" in subnet, "Invalid subnet."
    byte1, byte2, byte3, byte4 = map(int, subnet.split("/")[0].split("."))
    mask_n = int(subnet.split("/")[1])
    assert 0 <= mask_n <= 32, "Invalid subnet mask."
    ip = (byte1 << 24) | (byte2 << 16) | (byte3 << 8) | byte4
    ip = ip & (0xFFFFFFFF << (32 - mask_n))
    ip = ip | random.randint(0, 2 ** (32 - mask_n) - 2)  # -2 because -1 is reserved for broadcast
    ip_arr = [(ip >> 24) & 0xFF, (ip >> 16) & 0xFF, (ip >> 8) & 0xFF, ip & 0xFF]
    if ip_arr[0] == 0:
        return random_ip(subnet)
    return ".".join(map(str, ip_arr))


def broadcast_ip(subnet: str) -> str:
    assert "/" in subnet, "Invalid subnet."
    byte1, byte2, byte3, byte4 = map(int, subnet.split("/")[0].split("."))
    mask_n = int(subnet.split("/")[1])
    assert 0 <= mask_n <= 32, "Invalid subnet mask."
    ip = (byte1 << 24) | (byte2 << 16) | (byte3 << 8) | byte4
    ip = ip & (0xFFFFFFFF << (32 - mask_n))
    ip = ip | (0xFFFFFFFF >> mask_n)
    ip_arr = [(ip >> 24) & 0xFF, (ip >> 16) & 0xFF, (ip >> 8) & 0xFF, ip & 0xFF]
    return ".".join(map(str, ip_arr))
