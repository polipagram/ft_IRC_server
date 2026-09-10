#!/usr/bin/env python3

import socket
import time
import sys
import os
import signal
import subprocess
import tempfile
import shutil
import random
import string
import argparse
import re


HOST = "127.0.0.1"
PORT = 6667
PASSWORD = "00"
SERVER = "./irc"

TESTS = []
RUN_ID = "".join(random.choice(string.ascii_lowercase) for _ in range(2))
COUNTER = 0


# ============================================================
# CLIENT
# ============================================================

class IrcClient:
    def __init__(self, host=HOST, port=PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(2)
        self.sock.connect((host, port))
        self.sock.settimeout(0.05)
        self.buffer = ""

    def send(self, msg):
        self.sock.sendall((msg + "\r\n").encode())

    def clear(self):
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
            except socket.timeout:
                break
            except OSError:
                break

        self.buffer = ""

    def wait_for(self, text, timeout=2):
        end = time.time() + timeout

        while time.time() < end:
            if text in self.buffer:
                return True

            try:
                data = self.sock.recv(4096)

                if not data:
                    return text in self.buffer

                self.buffer += data.decode(errors="replace")

            except socket.timeout:
                pass
            except OSError:
                return text in self.buffer

        return text in self.buffer

    def wait_for_all(self, texts, timeout=2):
        end = time.time() + timeout

        while time.time() < end:
            if all(text in self.buffer for text in texts):
                return True

            try:
                data = self.sock.recv(4096)

                if not data:
                    break

                self.buffer += data.decode(errors="replace")

            except socket.timeout:
                pass
            except OSError:
                break

        return all(text in self.buffer for text in texts)

    def wait_closed(self, timeout=3):
        end = time.time() + timeout

        while time.time() < end:
            try:
                data = self.sock.recv(4096)

                if not data:
                    return True

                self.buffer += data.decode(errors="replace")

            except socket.timeout:
                pass
            except OSError:
                return True

        return False

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


# ============================================================
# HELPERS
# ============================================================

def uniq(prefix="u"):
    global COUNTER
    COUNTER += 1
    return (prefix + RUN_ID + str(COUNTER))[:9]


def result(ok, message=""):
    return {
        "ok": ok,
        "message": message
    }


def test(name):
    def decorator(func):
        TESTS.append((name, func))
        return func
    return decorator


def close_all(clients):
    for client in clients:
        client.close()


def new_client(host=None, port=None):
    if host is None:
        host = HOST
    if port is None:
        port = PORT

    nick = uniq()
    client = IrcClient(host, port)

    client.send("PASS " + PASSWORD)
    client.send("NICK " + nick)
    client.send("USER " + nick + " 0 * :" + nick)

    if not client.wait_for(" 001 "):
        client.close()
        raise RuntimeError(
            "registration failed\n" + client.buffer
        )

    client.clear()
    return client, nick


def free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def wait_server_up(port, timeout=10):
    end = time.time() + timeout

    while time.time() < end:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)

        try:
            sock.connect((HOST, port))
            sock.close()
            return True
        except OSError:
            sock.close()
            time.sleep(0.05)

    return False


def start_server(port, password, valgrind=False):
    server = os.path.abspath(SERVER)

    if not os.path.exists(server):
        raise RuntimeError("server executable not found: " + server)

    if not os.access(server, os.X_OK):
        raise RuntimeError("server is not executable: " + server)

    logfile = None
    log_file = None

    if valgrind:
        vg = shutil.which("valgrind")

        if not vg:
            raise RuntimeError("valgrind is not installed")

        logfile = tempfile.mktemp(
            prefix="irc_valgrind_",
            suffix=".log"
        )

        log_file = open(logfile, "w")

        cmd = [
            vg,
            "--leak-check=full",
            "--show-leak-kinds=all",
            "--errors-for-leak-kinds=definite,indirect",
            "--error-exitcode=42",
            server,
            str(port),
            password
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT
        )

        proc._log_file = log_file
        proc._log_path = logfile

    else:
        proc = subprocess.Popen(
            [server, str(port), password],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    if not wait_server_up(port, 10):
        if proc.poll() is None:
            proc.kill()
            proc.wait()

        if log_file:
            log_file.close()

        raise RuntimeError(
            "server did not start on port " + str(port)
        )

    return proc


def stop_server(proc):
    if proc is None:
        return

    if proc.poll() is None:
        try:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.terminate()

            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    if hasattr(proc, "_log_file"):
        try:
            proc._log_file.close()
        except Exception:
            pass


def read_valgrind_log(proc):
    if not hasattr(proc, "_log_path"):
        return ""

    path = proc._log_path

    if not os.path.exists(path):
        return ""

    try:
        with open(path, "r") as f:
            return f.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ============================================================
# 01 - 04 PASS
# ============================================================

@test("01 PASS: valid password")
def test_01():
    c = IrcClient()
    nick = uniq()

    try:
        c.send("PASS " + PASSWORD)
        c.send("NICK " + nick)
        c.send("USER " + nick + " 0 * :" + nick)

        return result(c.wait_for(" 001 "), c.buffer)
    finally:
        c.close()


@test("02 PASS: wrong password")
def test_02():
    c = IrcClient()
    nick = uniq()

    try:
        c.send("PASS WRONG")
        c.send("NICK " + nick)
        c.send("USER " + nick + " 0 * :" + nick)

        return result(c.wait_for(" 464 "), c.buffer)
    finally:
        c.close()


@test("03 PASS: missing password")
def test_03():
    c = IrcClient()
    nick = uniq()

    try:
        c.send("NICK " + nick)
        c.send("USER " + nick + " 0 * :" + nick)

        time.sleep(0.2)
        c.clear()

        return result(" 001 " not in c.buffer, c.buffer)
    finally:
        c.close()


@test("04 PASS: after registration")
def test_04():
    c, _ = new_client()

    try:
        c.send("PASS " + PASSWORD)
        return result(c.wait_for(" 462 "), c.buffer)
    finally:
        c.close()


# ============================================================
# 05 - 11 NICK / USER
# ============================================================

@test("05 NICK: missing parameter")
def test_05():
    c = IrcClient()

    try:
        c.send("NICK")

        ok = c.wait_for(" 431 ") or c.wait_for(" 461 ")

        return result(ok, c.buffer)
    finally:
        c.close()


@test("06 NICK: digit first")
def test_06():
    c = IrcClient()

    try:
        c.send("PASS " + PASSWORD)
        c.send("NICK 1abc")

        return result(c.wait_for(" 432 "), c.buffer)
    finally:
        c.close()


@test("07 NICK: invalid character")
def test_07():
    c = IrcClient()

    try:
        c.send("PASS " + PASSWORD)
        c.send("NICK abc!")

        return result(c.wait_for(" 432 "), c.buffer)
    finally:
        c.close()


@test("08 NICK: duplicate nickname")
def test_08():
    c1, nick = new_client()
    c2 = IrcClient()

    try:
        c2.send("PASS " + PASSWORD)
        c2.send("NICK " + nick)

        return result(c2.wait_for(" 433 "), c2.buffer)
    finally:
        c1.close()
        c2.close()


@test("09 NICK: registered nick change")
def test_09():
    c, oldnick = new_client()
    newnick = uniq()

    try:
        c.clear()
        c.send("NICK " + newnick)

        # RFC-style NICK reply normally contains:
        # :oldnick!user@host NICK :newnick
        ok = c.wait_for(" NICK ")

        return result(ok, c.buffer)
    finally:
        c.close()


@test("10 USER: missing parameter")
def test_10():
    c = IrcClient()

    try:
        c.send("PASS " + PASSWORD)
        c.send("NICK " + uniq())
        c.send("USER")

        return result(c.wait_for(" 461 "), c.buffer)
    finally:
        c.close()


@test("11 USER: second USER")
def test_11():
    c, _ = new_client()

    try:
        c.send("USER again 0 * :again")

        return result(c.wait_for(" 462 "), c.buffer)
    finally:
        c.close()


# ============================================================
# 12 - 17 JOIN
# ============================================================

@test("12 JOIN: missing parameter")
def test_12():
    c, _ = new_client()

    try:
        c.send("JOIN")
        return result(c.wait_for(" 461 "), c.buffer)
    finally:
        c.close()


@test("13 JOIN: invalid channel")
def test_13():
    c, _ = new_client()

    try:
        c.send("JOIN channel")
        return result(c.wait_for(" 403 "), c.buffer)
    finally:
        c.close()


@test("14 JOIN: create channel")
def test_14():
    c, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c.send("JOIN " + channel)
        return result(c.wait_for(" 366 "), c.buffer)
    finally:
        c.close()


@test("15 JOIN: comma separated")
def test_15():
    c, _ = new_client()
    ch1 = "#" + uniq("c")
    ch2 = "#" + uniq("c")

    try:
        c.send("JOIN " + ch1 + "," + ch2)
        return result(c.wait_for(" 403 "), c.buffer)
    finally:
        c.close()


@test("16 JOIN: channel 0")
def test_16():
    c, _ = new_client()

    try:
        c.send("JOIN 0")
        return result(c.wait_for(" 403 "), c.buffer)
    finally:
        c.close()


@test("17 JOIN: already joined")
def test_17():
    c, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c.send("JOIN " + channel)
        c.wait_for(" 366 ")
        c.clear()

        c.send("JOIN " + channel)

        return result(c.wait_for(" 443 "), c.buffer)
    finally:
        c.close()


# ============================================================
# 18 - 23 PRIVMSG
# ============================================================

@test("18 PRIVMSG: missing recipient")
def test_18():
    c, _ = new_client()

    try:
        c.send("PRIVMSG")

        ok = c.wait_for(" 411 ") or c.wait_for(" 461 ")

        return result(ok, c.buffer)
    finally:
        c.close()


@test("19 PRIVMSG: missing text")
def test_19():
    c, _ = new_client()

    try:
        c.send("PRIVMSG nobody")
        return result(c.wait_for(" 412 "), c.buffer)
    finally:
        c.close()


@test("20 PRIVMSG: unknown target")
def test_20():
    c, _ = new_client()

    try:
        c.send("PRIVMSG nobody123 :hello")
        return result(c.wait_for(" 401 "), c.buffer)
    finally:
        c.close()


@test("21 PRIVMSG: user to user")
def test_21():
    c1, _ = new_client()
    c2, n2 = new_client()

    try:
        c2.clear()
        c1.send("PRIVMSG " + n2 + " :hello")

        return result(c2.wait_for("hello"), c2.buffer)
    finally:
        close_all([c1, c2])


@test("22 PRIVMSG: channel broadcast")
def test_22():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c1.clear()
        c2.clear()

        c1.send("PRIVMSG " + channel + " :hello-channel")

        return result(
            c2.wait_for("hello-channel"),
            c2.buffer
        )
    finally:
        close_all([c1, c2])


@test("23 PRIVMSG: not joined")
def test_23():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.clear()
        c2.send("PRIVMSG " + channel + " :hello")

        ok = c2.wait_for(" 404 ") or c2.wait_for(" 442 ")

        return result(ok, c2.buffer)
    finally:
        close_all([c1, c2])


# ============================================================
# 24 - 27 TOPIC
# ============================================================

@test("24 TOPIC: missing parameter")
def test_24():
    c, _ = new_client()

    try:
        c.send("TOPIC")
        return result(c.wait_for(" 461 "), c.buffer)
    finally:
        c.close()


@test("25 TOPIC: empty topic")
def test_25():
    c, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c.send("JOIN " + channel)
        c.wait_for(" 366 ")
        c.clear()

        c.send("TOPIC " + channel)

        return result(c.wait_for(" 331 "), c.buffer)
    finally:
        c.close()


@test("26 TOPIC: set and query")
def test_26():
    c, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c.send("JOIN " + channel)
        c.wait_for(" 366 ")

        c.send("TOPIC " + channel + " :my-topic")
        c.wait_for(" 332 ")

        c.clear()
        c.send("TOPIC " + channel)

        return result(
            c.wait_for_all([" 332 ", "my-topic"]),
            c.buffer
        )
    finally:
        c.close()


@test("27 TOPIC: non-op with +t")
def test_27():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c1.send("MODE " + channel + " +t")
        c1.wait_for(" MODE ")

        c2.clear()
        c2.send("TOPIC " + channel + " :nope")

        return result(c2.wait_for(" 482 "), c2.buffer)
    finally:
        close_all([c1, c2])


# ============================================================
# 28 - 31 KICK
# ============================================================

@test("28 KICK: missing parameter")
def test_28():
    c, _ = new_client()

    try:
        c.send("KICK")
        return result(c.wait_for(" 461 "), c.buffer)
    finally:
        c.close()


@test("29 KICK: target not on channel")
def test_29():
    c, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c.send("JOIN " + channel)
        c.wait_for(" 366 ")
        c.clear()

        # Existing user target, but not a member of the channel.
        target, target_nick = new_client()

        try:
            c.clear()
            c.send("KICK " + channel + " " + target_nick)

            return result(
                c.wait_for(" 441 "),
                c.buffer
            )
        finally:
            target.close()

    finally:
        c.close()


@test("30 KICK: non-op")
def test_30():
    c1, _ = new_client()
    c2, n2 = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c2.clear()
        c2.send("KICK " + channel + " " + n2)

        return result(c2.wait_for(" 482 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("31 KICK: op kicks member")
def test_31():
    c1, _ = new_client()
    c2, n2 = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c1.clear()
        c2.clear()

        c1.send("KICK " + channel + " " + n2)

        return result(c2.wait_for(" KICK "), c2.buffer)
    finally:
        close_all([c1, c2])


# ============================================================
# 32 - 36 INVITE
# ============================================================

@test("32 INVITE: missing parameter")
def test_32():
    c, _ = new_client()

    try:
        c.send("INVITE")
        return result(c.wait_for(" 461 "), c.buffer)
    finally:
        c.close()


@test("33 INVITE: unknown nick")
def test_33():
    c, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c.send("JOIN " + channel)
        c.wait_for(" 366 ")
        c.clear()

        c.send("INVITE nobody " + channel)

        return result(c.wait_for(" 401 "), c.buffer)
    finally:
        c.close()


@test("34 INVITE: already in channel")
def test_34():
    c1, _ = new_client()
    c2, n2 = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c1.clear()
        c1.send("INVITE " + n2 + " " + channel)

        return result(c1.wait_for(" 443 "), c1.buffer)
    finally:
        close_all([c1, c2])


@test("35 INVITE: non-op on +i")
def test_35():
    c1, _ = new_client()
    c2, n2 = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c1.send("MODE " + channel + " +i")
        c1.wait_for(" MODE ")

        c2.clear()
        c2.send("INVITE " + n2 + " " + channel)

        return result(c2.wait_for(" 482 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("36 INVITE: op invites user")
def test_36():
    c1, _ = new_client()
    c2, n2 = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c1.send("MODE " + channel + " +i")
        c1.wait_for(" MODE ")

        c2.clear()
        c1.send("INVITE " + n2 + " " + channel)

        return result(c2.wait_for(" INVITE "), c2.buffer)
    finally:
        close_all([c1, c2])


# ============================================================
# 37 - 53 MODE
# ============================================================

@test("37 MODE: missing parameter")
def test_37():
    c, _ = new_client()

    try:
        c.send("MODE")
        return result(c.wait_for(" 461 "), c.buffer)
    finally:
        c.close()


@test("38 MODE: query")
def test_38():
    c, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c.send("JOIN " + channel)
        c.wait_for(" 366 ")
        c.clear()

        c.send("MODE " + channel)

        return result(c.wait_for(" 324 "), c.buffer)
    finally:
        c.close()


@test("39 MODE: unknown flag")
def test_39():
    c, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c.send("JOIN " + channel)
        c.wait_for(" 366 ")

        c.clear()
        c.send("MODE " + channel + " +z")

        return result(c.wait_for(" 472 "), c.buffer)
    finally:
        c.close()


@test("40 MODE: non-op")
def test_40():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c2.clear()
        c2.send("MODE " + channel + " +i")

        return result(c2.wait_for(" 482 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("41 MODE +i: join without invite")
def test_41():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c1.send("MODE " + channel + " +i")
        c1.wait_for(" MODE ")

        c2.send("JOIN " + channel)

        return result(c2.wait_for(" 473 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("42 MODE +i: invited join")
def test_42():
    c1, _ = new_client()
    c2, n2 = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c1.send("MODE " + channel + " +i")
        c1.wait_for(" MODE ")

        c2.clear()
        c1.send("INVITE " + n2 + " " + channel)
        c2.wait_for(" INVITE ")

        c2.clear()
        c2.send("JOIN " + channel)

        return result(c2.wait_for(" 366 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("43 MODE -i: join succeeds")
def test_43():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c1.send("MODE " + channel + " +i")
        c1.wait_for(" MODE ")

        c1.send("MODE " + channel + " -i")
        c1.wait_for(" MODE ")

        c2.send("JOIN " + channel)

        return result(c2.wait_for(" 366 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("44 MODE +t: non-op cannot set topic")
def test_44():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c1.send("MODE " + channel + " +t")
        c1.wait_for(" MODE ")

        c2.clear()
        c2.send("TOPIC " + channel + " :test")

        return result(c2.wait_for(" 482 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("45 MODE -t: non-op can set topic")
def test_45():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c1.send("MODE " + channel + " +t")
        c1.wait_for(" MODE ")

        c1.send("MODE " + channel + " -t")
        c1.wait_for(" MODE ")

        c2.clear()
        c2.send("TOPIC " + channel + " :allowed")

        return result(c2.wait_for(" 332 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("46 MODE +k: join without key")
def test_46():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c1.send("MODE " + channel + " +k secret")
        c1.wait_for(" MODE ")

        c2.send("JOIN " + channel)

        return result(c2.wait_for(" 475 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("47 MODE +k: correct key")
def test_47():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c1.send("MODE " + channel + " +k secret")
        c1.wait_for(" MODE ")

        c2.send("JOIN " + channel + " secret")

        return result(c2.wait_for(" 366 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("48 MODE -k: join without key")
def test_48():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c1.send("MODE " + channel + " +k secret")
        c1.wait_for(" MODE ")

        c1.send("MODE " + channel + " -k")
        c1.wait_for(" MODE ")

        c2.send("JOIN " + channel)

        return result(c2.wait_for(" 366 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("49 MODE +o: promoted user can KICK")
def test_49():
    c1, _ = new_client()
    c2, n2 = new_client()
    c3, n3 = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c3.send("JOIN " + channel)
        c3.wait_for(" 366 ")

        c1.send("MODE " + channel + " +o " + n2)
        c1.wait_for(" MODE ")

        c2.clear()
        c3.clear()

        c2.send("KICK " + channel + " " + n3)

        return result(c3.wait_for(" KICK "), c3.buffer)
    finally:
        close_all([c1, c2, c3])


@test("50 MODE -o: demoted user cannot KICK")
def test_50():
    c1, _ = new_client()
    c2, n2 = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c1.send("MODE " + channel + " +o " + n2)
        c1.wait_for(" MODE ")

        c1.send("MODE " + channel + " -o " + n2)
        c1.wait_for(" MODE ")

        c2.clear()
        c2.send("KICK " + channel + " " + n2)

        return result(c2.wait_for(" 482 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("51 MODE +o: target not in channel")
def test_51():
    c1, _ = new_client()
    c2, n2 = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c1.clear()
        c1.send("MODE " + channel + " +o " + n2)

        ok = c1.wait_for(" 441 ") or c1.wait_for(" 401 ")

        return result(ok, c1.buffer)
    finally:
        close_all([c1, c2])


@test("52 MODE +l: channel limit")
def test_52():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c1.send("MODE " + channel + " +l 1")
        c1.wait_for(" MODE ")

        c2.send("JOIN " + channel)

        return result(c2.wait_for(" 471 "), c2.buffer)
    finally:
        close_all([c1, c2])


@test("53 MODE -l: remove limit")
def test_53():
    c1, _ = new_client()
    c2, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c1.send("MODE " + channel + " +l 1")
        c1.wait_for(" MODE ")

        c1.send("MODE " + channel + " -l")
        c1.wait_for(" MODE ")

        c2.send("JOIN " + channel)

        return result(c2.wait_for(" 366 "), c2.buffer)
    finally:
        close_all([c1, c2])


# ============================================================
# 54 - 57 MULTI CLIENT / CLEANUP
# ============================================================

@test("54 five clients JOIN same channel")
def test_54():
    clients = []
    channel = "#" + uniq("c")

    try:
        for _ in range(5):
            c, _ = new_client()
            clients.append(c)

        for c in clients:
            c.send("JOIN " + channel)

        ok = True

        for c in clients:
            ok = ok and c.wait_for(" 366 ")

        return result(ok)

    finally:
        close_all(clients)


@test("55 five clients channel PRIVMSG")
def test_55():
    clients = []
    channel = "#" + uniq("c")

    try:
        for _ in range(5):
            c, _ = new_client()
            clients.append(c)

        for c in clients:
            c.send("JOIN " + channel)

        for c in clients:
            c.wait_for(" 366 ")
            c.clear()

        clients[0].send(
            "PRIVMSG " + channel + " :broadcast-test"
        )

        ok = True

        for c in clients[1:]:
            ok = ok and c.wait_for("broadcast-test")

        return result(ok)

    finally:
        close_all(clients)


@test("56 KICK broadcast")
def test_56():
    c1, _ = new_client()
    c2, n2 = new_client()
    c3, _ = new_client()
    channel = "#" + uniq("c")

    try:
        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c3.send("JOIN " + channel)
        c3.wait_for(" 366 ")

        c1.clear()
        c2.clear()
        c3.clear()

        c1.send("KICK " + channel + " " + n2)

        ok = c1.wait_for(" KICK ")
        ok = ok and c2.wait_for(" KICK ")
        ok = ok and c3.wait_for(" KICK ")

        return result(ok)

    finally:
        close_all([c1, c2, c3])


@test("57 closed client frees nickname")
def test_57():
    c1, nick = new_client()

    try:
        c1.close()
        time.sleep(0.3)

        c2 = IrcClient()

        try:
            c2.send("PASS " + PASSWORD)
            c2.send("NICK " + nick)
            c2.send("USER " + nick + " 0 * :" + nick)

            return result(c2.wait_for(" 001 "), c2.buffer)

        finally:
            c2.close()

    except Exception as e:
        return result(False, str(e))


# ============================================================
# 58 SHUTDOWN
# ============================================================

@test("58 SHUTDOWN: SIGINT closes server and clients")
def test_58():
    port = free_port()
    proc = None
    clients = []

    try:
        proc = start_server(port, PASSWORD)

        for _ in range(3):
            c, _ = new_client(port=port)
            clients.append(c)

        proc.send_signal(signal.SIGINT)

        try:
            proc.wait(timeout=8)
            exited = True
        except subprocess.TimeoutExpired:
            exited = False

        closed = all(
            c.wait_closed(3)
            for c in clients
        )

        return result(
            exited and closed,
            "server exited=%s clients_closed=%s"
            % (exited, closed)
        )

    except Exception as e:
        return result(False, str(e))

    finally:
        close_all(clients)
        stop_server(proc)


# ============================================================
# 59 SHUTDOWN / RESTART
# ============================================================

@test("59 SHUTDOWN: port reusable after SIGINT")
def test_59():
    port = free_port()
    proc1 = None
    proc2 = None

    try:
        proc1 = start_server(port, PASSWORD)

        c = IrcClient(HOST, port)
        c.close()

        proc1.send_signal(signal.SIGINT)
        proc1.wait(timeout=8)

        if proc1.poll() is None:
            return result(False, "first server still running")

        proc2 = start_server(port, PASSWORD)

        return result(
            proc2.poll() is None,
            "second server could not stay running"
        )

    except Exception as e:
        return result(False, str(e))

    finally:
        stop_server(proc1)
        stop_server(proc2)


# ============================================================
# 60 SHUTDOWN / NEW CONNECTION
# ============================================================

@test("60 SHUTDOWN: new connections rejected")
def test_60():
    port = free_port()
    proc = None

    try:
        proc = start_server(port, PASSWORD)

        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=8)

        if proc.poll() is None:
            return result(False, "server still running")

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )
        sock.settimeout(1)

        try:
            sock.connect((HOST, port))
            sock.close()

            return result(
                False,
                "connection accepted after shutdown"
            )

        except OSError:
            sock.close()
            return result(True)

    except Exception as e:
        return result(False, str(e))

    finally:
        stop_server(proc)


# ============================================================
# 61 VALGRIND / LEAKS
# ============================================================

@test("61 LEAKS: Valgrind clean shutdown")
def test_61():
    if not shutil.which("valgrind"):
        return result(
            None,
            "valgrind is not installed"
        )

    port = free_port()
    proc = None
    clients = []

    try:
        proc = start_server(
            port,
            PASSWORD,
            valgrind=True
        )

        # Create several clients and exercise allocations.
        c1, n1 = new_client(port=port)
        c2, n2 = new_client(port=port)
        c3, n3 = new_client(port=port)

        clients = [c1, c2, c3]

        channel = "#" + uniq("v")

        c1.send("JOIN " + channel)
        c1.wait_for(" 366 ")

        c2.send("JOIN " + channel)
        c2.wait_for(" 366 ")

        c3.send("JOIN " + channel)
        c3.wait_for(" 366 ")

        c1.send("MODE " + channel + " +i")
        c1.wait_for(" MODE ")

        c1.send("MODE " + channel + " +t")
        c1.wait_for(" MODE ")

        c1.send(
            "PRIVMSG " + channel + " :valgrind-test"
        )

        c2.wait_for("valgrind-test")
        c3.wait_for("valgrind-test")

        c1.send(
            "MODE " + channel + " +o " + n2
        )
        c1.wait_for(" MODE ")

        c2.send(
            "TOPIC " + channel + " :valgrind-topic"
        )
        c2.wait_for(" 332 ")

        c2.send(
            "INVITE " + n3 + " " + channel
        )
        c3.wait_for(" INVITE ")

        # Shutdown is important:
        # Valgrind checks memory at process exit.
        proc.send_signal(signal.SIGINT)

        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

            return result(
                False,
                "Valgrind/server did not exit"
            )

        # Close the output file before reading it.
        if hasattr(proc, "_log_file"):
            proc._log_file.close()

        output = read_valgrind_log(proc)

        if not output:
            return result(
                False,
                "Valgrind output is empty"
            )

        # ----------------------------------------------------
        # Robust Valgrind parsing
        # ----------------------------------------------------

        definitely_zero = bool(
            re.search(
                r"definitely lost:\s*0 bytes in 0 blocks",
                output
            )
        )

        indirectly_zero = bool(
            re.search(
                r"indirectly lost:\s*0 bytes in 0 blocks",
                output
            )
        )

        error_summary_zero = bool(
            re.search(
                r"ERROR SUMMARY:\s*0 errors from 0 contexts",
                output
            )
        )

        all_freed = (
            "All heap blocks were freed -- no leaks are possible"
            in output
        )

        # With --error-exitcode=42, a definite/indirect leak
        # should also make Valgrind return 42.
        exit_clean = proc.returncode == 0

        leaks_clean = (
            all_freed
            or (
                definitely_zero
                and indirectly_zero
            )
        )

        ok = (
            leaks_clean
            and error_summary_zero
            and exit_clean
        )

        if ok:
            return result(
                True,
                "Valgrind: 0 bytes leaked, 0 errors"
            )

        # Show useful Valgrind lines when something goes wrong.
        important = []

        for line in output.splitlines():
            if (
                "HEAP SUMMARY" in line
                or "in use at exit:" in line
                or "definitely lost:" in line
                or "indirectly lost:" in line
                or "possibly lost:" in line
                or "All heap blocks were freed" in line
                or "ERROR SUMMARY:" in line
            ):
                important.append(line.strip())

        return result(
            False,
            "Valgrind failed:\n" +
            "\n".join(important)
        )

    except Exception as e:
        return result(False, str(e))

    finally:
        close_all(clients)
        stop_server(proc)


# ============================================================
# RUNNER
# ============================================================

def main():
    global HOST
    global PORT
    global PASSWORD
    global SERVER

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "host",
        nargs="?",
        default=HOST
    )

    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=PORT
    )

    parser.add_argument(
        "password",
        nargs="?",
        default=PASSWORD
    )

    parser.add_argument(
        "--server",
        default=SERVER
    )

    parser.add_argument(
        "--no-leaks",
        action="store_true",
        help="skip Valgrind test"
    )

    args = parser.parse_args()

    HOST = args.host
    PORT = args.port
    PASSWORD = args.password
    SERVER = args.server

    passed = 0
    failed = 0
    skipped = 0

    print("=" * 70)
    print("ft_irc tester")
    print("=" * 70)
    print("Server :", SERVER)
    print("Host   :", HOST)
    print("Port   :", PORT)
    print("=" * 70)

    for number, (name, func) in enumerate(TESTS, 1):

        if number == 61 and args.no_leaks:
            print("[SKIP] " + name + " (--no-leaks)")
            skipped += 1
            continue

        try:
            r = func()

            if r["ok"] is True:
                print("[PASS] " + name)
                passed += 1

            elif r["ok"] is None:
                print("[SKIP] " + name)
                print("       " + r["message"])
                skipped += 1

            else:
                print("[FAIL] " + name)

                if r["message"]:
                    for line in r["message"].splitlines():
                        print("       " + line)

                failed += 1

        except Exception as e:
            print("[FAIL] " + name)
            print("       " + str(e))
            failed += 1

    print()
    print("=" * 70)
    print(
        "RESULT: PASS=%d FAIL=%d SKIP=%d TOTAL=%d"
        % (
            passed,
            failed,
            skipped,
            len(TESTS)
        )
    )
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())