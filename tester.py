#!/usr/bin/env python3
"""
ft_irc tester — 57 tests covering PASS, NICK, USER, JOIN, PRIVMSG, TOPIC,
KICK, INVITE and every MODE flag (+i/-i, +t/-t, +k/-k, +o/-o, +l/-l).

Adjusted to match this server's actual command set: dispatchCommand only
recognizes PASS/NICK/USER/JOIN/PRIVMSG/TOPIC/KICK/INVITE/MODE. There is no
QUIT and no PART handler, and JOIN only ever reads params[0] as a single
channel name (no comma-split, no "JOIN 0" special case) — a comma in the
name just fails validChannelName() like any other invalid character.

Usage:
    python3 tester.py [host] [port] [password]
Defaults:
    127.0.0.1 6667 pass
"""
import socket
import time
import sys
import difflib
import random
import string


HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 6667
PASSWORD = sys.argv[3] if len(sys.argv) > 3 else "00"


class C:
    OK   = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    DIM  = "\033[2m"
    END  = "\033[0m"


# ===========================================================================
# IRC client
# ===========================================================================
class IrcClient:
    def __init__(self, host=HOST, port=PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(2.0)
        try:
            self.sock.connect((host, port))
        except Exception as e:
            raise ConnectionError(f"Cannot connect to {host}:{port} - {e}")
        self.sock.settimeout(0.05)
        self.buffer = ""

    def send(self, msg):
        if not msg.endswith("\r\n"):
            msg += "\r\n"
        try:
            self.sock.sendall(msg.encode("utf-8", errors="ignore"))
        except Exception:
            pass

    def _drain(self, duration=0.1):
        deadline = time.time() + duration
        while time.time() < deadline:
            try:
                data = self.sock.recv(4096)
                if not data:
                    # Peer closed the connection. Back off briefly instead
                    # of returning immediately, otherwise a caller looping
                    # in wait_for()/wait_for_all() would spin tight (recv
                    # on a closed socket returns instantly) for the rest
                    # of its timeout window.
                    time.sleep(0.02)
                    return
                self.buffer += data.decode("utf-8", errors="ignore")
            except socket.timeout:
                pass
            except Exception:
                time.sleep(0.02)
                return

    def wait_for(self, patterns, timeout=2.0):
        if isinstance(patterns, str):
            patterns = [patterns]
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._drain(0.1)
            if any(p in self.buffer for p in patterns):
                return True
        return False

    def wait_for_all(self, patterns, timeout=2.0):
        if isinstance(patterns, str):
            patterns = [patterns]
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._drain(0.1)
            if all(p in self.buffer for p in patterns):
                return True
        return False

    def clear(self):
        self._drain(0.05)
        self.buffer = ""

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


# ===========================================================================
# Helpers
# ===========================================================================
_counter = 0
# Random 2-letter run id: keeps nicknames unique across repeated invocations
# of this script against a still-running server (e.g. a previous run's
# connections haven't fully cleaned up yet) without needing a timestamp.
_run_id = "".join(random.choices(string.ascii_lowercase, k=2))


def uniq(prefix="u"):
    """Generate a short, collision-safe identifier.

    Kept deliberately compact (prefix + 2-letter run id + counter) so
    that even the longest prefixes used below stay comfortably under
    the 9-character nick length this server enforces (checkNickValid
    rejects anything longer than 9 chars).
    """
    global _counter
    _counter += 1
    return f"{prefix}{_run_id}{_counter}"


def login(client, nick, password=PASSWORD):
    client.send(f"PASS {password}")
    client.send(f"NICK {nick}")
    client.send(f"USER {nick} 0 * :{nick}")
    return client.wait_for(" 001 ", timeout=2.0)


def new_client(nick=None):
    c = IrcClient()
    n = nick or uniq("n")
    if not login(c, n):
        c.close()
        raise RuntimeError(f"login failed for {n}: {c.buffer!r}")
    c.nick = n
    c.clear()
    return c, n


# ===========================================================================
# Result + simple runner
# ===========================================================================
class Result:
    def __init__(self, name):
        self.name = name
        self.ok = False
        self.expected = ""
        self.actual = ""
        self.error = ""

    def pass_(self):
        self.ok = True
        return self

    def fail(self, expected, actual, error=""):
        self.ok = False
        self.expected = expected
        self.actual = actual
        self.error = error
        return self


def simple_test(name, commands, expected_patterns, timeout=2.0):
    r = Result(name)
    r.expected = " | ".join(expected_patterns)
    c = None
    try:
        c = IrcClient()
        for cmd in commands:
            c.send(cmd)
            time.sleep(0.05)
        if c.wait_for(expected_patterns, timeout=timeout):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "(exception)", str(e))
    finally:
        if c:
            c.close()


# ===========================================================================
# Tests
# ===========================================================================
TESTS = []


def register(name):
    def deco(fn):
        TESTS.append((name, fn))
        return fn
    return deco


# ============================ PASS / NICK / USER ===========================

@register("01. PASS - valid password allows registration")
def t():
    n = uniq("ps")
    return simple_test("01",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}"],
        [" 001 "])


@register("02. PASS - wrong password -> 464")
def t():
    n = uniq("bd")
    return simple_test("02",
        [f"PASS wrong_{PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}"],
        ["464"])


@register("03. PASS - missing password, registration refused")
def t():
    n = uniq("np")
    r = Result("03")
    r.expected = "no 001 (registration refused)"
    c = None
    try:
        c = IrcClient()
        c.send(f"NICK {n}")
        c.send(f"USER {n} 0 * :{n}")
        c.wait_for(" 001 ", timeout=2.0)
        if " 001 " not in c.buffer:
            return r.pass_()
        return r.fail(r.expected, c.buffer)
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c:
            c.close()


@register("04. PASS - re-sending PASS after registration -> 462")
def t():
    n = uniq("dp")
    return simple_test("04",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}",
         f"PASS {PASSWORD}"],
        ["462"])


@register("05. NICK - missing parameter -> 431")
def t():
    n = uniq("n")
    return simple_test("05",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}", "NICK"],
        ["431", "461"])


@register("06. NICK - nickname starting with digit -> 432")
def t():
    n = uniq("n")
    return simple_test("06",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}",
         "NICK 9bad"],
        ["432"])


@register("07. NICK - nickname with invalid char '!' -> 432")
def t():
    n = uniq("n")
    return simple_test("07",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}",
         "NICK bad!name"],
        ["432"])


@register("08. NICK - duplicate nickname -> 433")
def t():
    r = Result("08")
    r.expected = "433 ERR_NICKNAMEINUSE"
    n1 = uniq("a")
    c1 = c2 = None
    try:
        c1 = IrcClient(); login(c1, n1); c1.clear()
        c2 = IrcClient()
        c2.send(f"PASS {PASSWORD}")
        c2.send(f"NICK {n1}")
        c2.send("USER other 0 * :other")
        if c2.wait_for("433", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("09. NICK - valid change after registration")
def t():
    r = Result("09")
    n = uniq("ch")
    n2 = uniq("cx")
    r.expected = f"NICK {n2}"
    c = None
    try:
        c = IrcClient(); login(c, n); c.clear()
        c.send(f"NICK {n2}")
        if c.wait_for([f"NICK {n2}", f"NICK :{n2}"], timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c: c.close()


@register("10. USER - missing parameters -> 461")
def t():
    n = uniq("u")
    return simple_test("10",
        [f"PASS {PASSWORD}", f"NICK {n}", "USER only"],
        ["461"])


@register("11. USER - second USER after registration -> 462")
def t():
    n = uniq("u")
    return simple_test("11",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}",
         "USER a 0 * :b"],
        ["462"])


# =================================== JOIN ==================================

@register("12. JOIN - no parameter -> 461")
def t():
    n = uniq("j")
    return simple_test("12",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}", "JOIN"],
        ["461"])


@register("13. JOIN - channel name without '#' -> 403")
def t():
    n = uniq("j")
    return simple_test("13",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}",
         "JOIN badchan"],
        ["403"])


@register("14. JOIN - create channel + receive 366")
def t():
    r = Result("14")
    ch = "#" + uniq("c")
    r.expected = f"JOIN {ch} + 366 RPL_ENDOFNAMES"
    c = None
    try:
        c, _ = new_client()
        c.send(f"JOIN {ch}")
        if c.wait_for_all([ch, "366"], timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c: c.close()


@register("15. JOIN - comma-separated channel name -> 403 (no multi-JOIN support)")
def t():
    # joinHandler treats message.params[0] as a single channel name; it
    # never splits on ','. validChannelName() explicitly rejects commas,
    # so "#a,#b" is just an invalid channel name here, not two JOINs.
    r = Result("15")
    ch1, ch2 = "#" + uniq("c"), "#" + uniq("c")
    r.expected = "403 ERR_NOSUCHCHANNEL (comma treated as invalid char)"
    c = None
    try:
        c, _ = new_client()
        c.send(f"JOIN {ch1},{ch2}")
        if c.wait_for("403", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c: c.close()


@register("16. JOIN 0 - not special-cased -> 403 (invalid channel name)")
def t():
    # No PART/JOIN-0 "leave everything" behavior exists; "0" simply fails
    # validChannelName() (doesn't start with '#') like any other bad name.
    r = Result("16")
    r.expected = "403 ERR_NOSUCHCHANNEL"
    c = None
    try:
        c, _ = new_client()
        c.send("JOIN 0")
        if c.wait_for("403", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c: c.close()


@register("17. JOIN - joining an already-joined channel -> 443 (no PART to leave first)")
def t():
    # There's no PART handler, so the only way this server lets a client
    # "rejoin" a channel it's already in is to just try JOIN again, which
    # joinHandler explicitly rejects via hasMember() -> 443.
    r = Result("17")
    ch = "#" + uniq("c")
    r.expected = "443 ERR_USERONCHANNEL on duplicate JOIN"
    c = None
    try:
        c, _ = new_client()
        c.send(f"JOIN {ch}"); c.wait_for("366", 2.0); c.clear()
        c.send(f"JOIN {ch}")
        if c.wait_for("443", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c: c.close()


# ================================= PRIVMSG =================================

@register("18. PRIVMSG - no recipient -> 411/461")
def t():
    n = uniq("p")
    return simple_test("18",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}", "PRIVMSG"],
        ["411", "461"])


@register("19. PRIVMSG - no text -> 412")
def t():
    n = uniq("p")
    return simple_test("19",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}",
         f"PRIVMSG {n}"],
        ["412"])


@register("20. PRIVMSG - unknown target -> 401")
def t():
    n = uniq("p")
    return simple_test("20",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}",
         f"PRIVMSG gh{uniq()} :hi"],
        ["401"])


@register("21. PRIVMSG - user to user delivery")
def t():
    r = Result("21")
    r.expected = "PRIVMSG delivered to target"
    c1 = c2 = None
    try:
        c1, n1 = new_client()
        c2, _  = new_client()
        c1.send(f"PRIVMSG {c2.nick} :hello-from-{n1}")
        if c2.wait_for(f"hello-from-{n1}", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("22. PRIVMSG - channel broadcast reaches peer")
def t():
    r = Result("22")
    r.expected = "channel PRIVMSG reaches other member"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c2.send(f"JOIN {ch}"); c2.wait_for("366", 2.0)
        time.sleep(0.3)
        c2.clear()
        c1.send(f"PRIVMSG {ch} :broadcast-msg")
        if c2.wait_for("broadcast-msg", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("23. PRIVMSG - channel not joined -> 404/442")
def t():
    n = uniq("p")
    ch = "#" + uniq("c")
    return simple_test("23",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}",
         f"PRIVMSG {ch} :hi"],
        ["404", "442"])


# =================================== TOPIC ==================================

@register("24. TOPIC - no parameter -> 461")
def t():
    n = uniq("t")
    return simple_test("24",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}", "TOPIC"],
        ["461"])


@register("25. TOPIC - query on empty channel -> 331")
def t():
    r = Result("25")
    ch = "#" + uniq("c")
    r.expected = "331 RPL_NOTOPIC"
    c = None
    try:
        c, _ = new_client()
        c.send(f"JOIN {ch}"); c.wait_for("366", 2.0); c.clear()
        c.send(f"TOPIC {ch}")
        if c.wait_for("331", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c: c.close()


@register("26. TOPIC - set then query -> 332 with topic text")
def t():
    r = Result("26")
    ch = "#" + uniq("c")
    topic = "my-fancy-topic"
    r.expected = f"332 RPL_TOPIC with '{topic}'"
    c = None
    try:
        c, _ = new_client()
        c.send(f"JOIN {ch}"); c.wait_for("366", 2.0); c.clear()
        c.send(f"TOPIC {ch} :{topic}")
        c.wait_for("TOPIC", 2.0); c.clear()
        c.send(f"TOPIC {ch}")
        if c.wait_for_all(["332", topic], timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c: c.close()


@register("27. TOPIC - non-op on +t channel -> 482")
def t():
    r = Result("27")
    r.expected = "482 ERR_CHANOPRIVSNEEDED"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c2.send(f"JOIN {ch}"); c2.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +t"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"TOPIC {ch} :nope")
        if c2.wait_for("482", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


# =================================== KICK ===================================

@register("28. KICK - no parameter -> 461")
def t():
    n = uniq("k")
    return simple_test("28",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}", "KICK"],
        ["461"])


@register("29. KICK - target not on channel -> 441")
def t():
    r = Result("29")
    r.expected = "441 ERR_USERNOTINCHANNEL"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, n2 = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0); c1.clear()
        c1.send(f"KICK {ch} {n2} :bye")
        if c1.wait_for("441", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c1.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("30. KICK - non-op tries to kick -> 482")
def t():
    r = Result("30")
    r.expected = "482 ERR_CHANOPRIVSNEEDED"
    c1 = c2 = None
    try:
        c1, n1 = new_client()
        c2, _  = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c2.send(f"JOIN {ch}"); c2.wait_for("366", 2.0)
        c2.clear()
        c2.send(f"KICK {ch} {n1} :nope")
        if c2.wait_for("482", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("31. KICK - op kicks member -> broadcast to victim")
def t():
    r = Result("31")
    r.expected = "KICK <chan> <nick> :reason on target"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, n2 = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c2.send(f"JOIN {ch}"); c2.wait_for("366", 2.0)
        time.sleep(0.3); c2.clear()
        c1.send(f"KICK {ch} {n2} :you-are-out")
        if c2.wait_for_all(["KICK", n2, "you-are-out"], timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


# ================================== INVITE ==================================

@register("32. INVITE - no parameter -> 461")
def t():
    n = uniq("i")
    return simple_test("32",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}", "INVITE"],
        ["461"])


@register("33. INVITE - unknown nickname -> 401")
def t():
    r = Result("33")
    ch = "#" + uniq("c")
    r.expected = "401 ERR_NOSUCHNICK"
    c = None
    try:
        c, _ = new_client()
        c.send(f"JOIN {ch}"); c.wait_for("366", 2.0); c.clear()
        c.send(f"INVITE gh{uniq()} {ch}")
        if c.wait_for("401", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c: c.close()


@register("34. INVITE - target already on channel -> 443")
def t():
    r = Result("34")
    r.expected = "443 ERR_USERONCHANNEL"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c2.send(f"JOIN {ch}"); c2.wait_for("366", 2.0)
        c1.clear()
        c1.send(f"INVITE {c2.nick} {ch}")
        if c1.wait_for("443", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c1.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("35. INVITE - non-op tries to invite on +i -> 482")
def t():
    r = Result("35")
    r.expected = "482 ERR_CHANOPRIVSNEEDED"
    c1 = c2 = c3 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        c3, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c2.send(f"JOIN {ch}"); c2.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +i"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"INVITE {c3.nick} {ch}")
        if c2.wait_for("482", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        for x in (c1, c2, c3):
            if x: x.close()


@register("36. INVITE - op invites user -> target notified")
def t():
    r = Result("36")
    r.expected = "INVITE received by target"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        time.sleep(0.3); c2.clear()
        c1.send(f"INVITE {c2.nick} {ch}")
        if c2.wait_for_all(["INVITE", ch], timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


# =================================== MODE ===================================

@register("37. MODE - no parameter -> 461")
def t():
    n = uniq("m")
    return simple_test("37",
        [f"PASS {PASSWORD}", f"NICK {n}", f"USER {n} 0 * :{n}", "MODE"],
        ["461"])


@register("38. MODE - query returns 324")
def t():
    r = Result("38")
    ch = "#" + uniq("c")
    r.expected = "324 RPL_CHANNELMODEIS"
    c = None
    try:
        c, _ = new_client()
        c.send(f"JOIN {ch}"); c.wait_for("366", 2.0); c.clear()
        c.send(f"MODE {ch}")
        if c.wait_for("324", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c: c.close()


@register("39. MODE - unknown flag -> 472")
def t():
    r = Result("39")
    ch = "#" + uniq("c")
    r.expected = "472 ERR_UNKNOWNMODE"
    c = None
    try:
        c, _ = new_client()
        c.send(f"JOIN {ch}"); c.wait_for("366", 2.0); c.clear()
        c.send(f"MODE {ch} +z")
        if c.wait_for("472", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c: c.close()


@register("40. MODE - non-op tries to change -> 482")
def t():
    r = Result("40")
    r.expected = "482 ERR_CHANOPRIVSNEEDED"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c2.send(f"JOIN {ch}"); c2.wait_for("366", 2.0)
        c2.clear()
        c2.send(f"MODE {ch} +i")
        if c2.wait_for("482", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


# ------------------------- MODE +i / -i (invite only) ----------------------

@register("41. MODE +i - join without invite -> 473")
def t():
    r = Result("41")
    r.expected = "473 ERR_INVITEONLYCHAN"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +i"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"JOIN {ch}")
        if c2.wait_for("473", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("42. MODE +i - join after INVITE succeeds")
def t():
    r = Result("42")
    r.expected = "JOIN ok after INVITE"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +i"); c1.wait_for("MODE", 1.5)
        c1.send(f"INVITE {c2.nick} {ch}")
        c2.wait_for("INVITE", 2.0); c2.clear()
        c2.send(f"JOIN {ch}")
        if c2.wait_for("366", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("43. MODE -i - everyone can join again")
def t():
    r = Result("43")
    r.expected = "JOIN ok after -i"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +i"); c1.wait_for("MODE", 1.5)
        c1.send(f"MODE {ch} -i"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"JOIN {ch}")
        if c2.wait_for("366", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


# ------------------------- MODE +t / -t (topic lock) -----------------------

@register("44. MODE +t - non-op TOPIC refused -> 482")
def t():
    r = Result("44")
    r.expected = "482 after +t for non-op TOPIC"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c2.send(f"JOIN {ch}"); c2.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +t"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"TOPIC {ch} :nope")
        if c2.wait_for("482", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("45. MODE -t - non-op TOPIC allowed again")
def t():
    r = Result("45")
    r.expected = "TOPIC broadcast after -t"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c2.send(f"JOIN {ch}"); c2.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +t"); c1.wait_for("MODE", 1.5)
        c1.send(f"MODE {ch} -t"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"TOPIC {ch} :allowed-now")
        if c2.wait_for("TOPIC", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


# ------------------------- MODE +k / -k (channel key) ----------------------

@register("46. MODE +k - join without key -> 475")
def t():
    r = Result("46")
    r.expected = "475 ERR_BADCHANNELKEY"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +k secretkey"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"JOIN {ch}")
        if c2.wait_for("475", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("47. MODE +k - join with correct key succeeds")
def t():
    r = Result("47")
    r.expected = "JOIN ok with correct key"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +k secretkey"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"JOIN {ch} secretkey")
        if c2.wait_for("366", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("48. MODE -k - key removed (join without key ok)")
def t():
    r = Result("48")
    r.expected = "JOIN ok after -k"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +k secretkey"); c1.wait_for("MODE", 1.5)
        c1.send(f"MODE {ch} -k secretkey"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"JOIN {ch}")
        if c2.wait_for("366", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


# ------------------------- MODE +o / -o (operator) -------------------------

@register("49. MODE +o - promoted user can KICK")
def t():
    r = Result("49")
    r.expected = "after +o, new op can KICK"
    c1 = c2 = c3 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        c3, n3 = new_client()
        ch = "#" + uniq("c")
        for cli in (c1, c2, c3):
            cli.send(f"JOIN {ch}"); cli.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +o {c2.nick}")
        c2.wait_for("MODE", 1.5); time.sleep(0.3)
        c3.clear()
        c2.send(f"KICK {ch} {n3} :promoted-kick")
        if c3.wait_for("KICK", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c3.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        for x in (c1, c2, c3):
            if x: x.close()


@register("50. MODE -o - demoted user can't KICK anymore")
def t():
    r = Result("50")
    r.expected = "482 after -o"
    c1 = c2 = c3 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        c3, n3 = new_client()
        ch = "#" + uniq("c")
        for cli in (c1, c2, c3):
            cli.send(f"JOIN {ch}"); cli.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +o {c2.nick}"); c1.wait_for("MODE", 1.5)
        c1.send(f"MODE {ch} -o {c2.nick}"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"KICK {ch} {n3} :nope")
        if c2.wait_for("482", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        for x in (c1, c2, c3):
            if x: x.close()


@register("51. MODE +o - target not in channel -> 441/401")
def t():
    r = Result("51")
    r.expected = "441 ERR_USERNOTINCHANNEL (or 401)"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, n2 = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0); c1.clear()
        c1.send(f"MODE {ch} +o {n2}")
        if c1.wait_for(["441", "401"], timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c1.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


# ------------------------- MODE +l / -l (user limit) -----------------------

@register("52. MODE +l - user limit enforced -> 471")
def t():
    r = Result("52")
    r.expected = "471 ERR_CHANNELISFULL"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +l 1"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"JOIN {ch}")
        if c2.wait_for("471", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


@register("53. MODE -l - limit removed, join succeeds")
def t():
    r = Result("53")
    r.expected = "JOIN ok after -l"
    c1 = c2 = None
    try:
        c1, _ = new_client()
        c2, _ = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c1.send(f"MODE {ch} +l 1"); c1.wait_for("MODE", 1.5)
        c1.send(f"MODE {ch} -l"); c1.wait_for("MODE", 1.5)
        time.sleep(0.3); c2.clear()
        c2.send(f"JOIN {ch}")
        if c2.wait_for("366", timeout=2.0):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


# ============================ MULTI-CLIENT TESTS ===========================

@register("54. MULTI - 5 clients JOIN same channel, all notified")
def t():
    r = Result("54")
    r.expected = "all 5 clients see JOIN broadcast + channel name"
    clients = []
    try:
        ch = "#" + uniq("c")
        for _ in range(5):
            c, _ = new_client()
            clients.append(c)
        for c in clients:
            c.send(f"JOIN {ch}")
        time.sleep(0.5)
        for c in clients:
            c.wait_for("366", timeout=2.0)
        ok = all(("JOIN" in c.buffer and ch in c.buffer) for c in clients)
        if ok:
            return r.pass_()
        snapshot = "\n".join(
            f"client{i}: {c.buffer[:120]!r}" for i, c in enumerate(clients)
        )
        return r.fail(r.expected, snapshot)
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        for c in clients:
            c.close()


@register("55. MULTI - PRIVMSG broadcast to 4 other clients")
def t():
    r = Result("55")
    r.expected = "all 4 peers received the channel message"
    clients = []
    try:
        ch = "#" + uniq("c")
        for _ in range(5):
            c, _ = new_client()
            clients.append(c)
        for c in clients:
            c.send(f"JOIN {ch}"); c.wait_for("366", 2.0)
        time.sleep(0.3)
        for c in clients:
            c.clear()
        msg = "hello-multi-" + uniq()
        clients[0].send(f"PRIVMSG {ch} :{msg}")
        time.sleep(0.5)
        ok = all(c.wait_for(msg, timeout=2.0) for c in clients[1:])
        if ok:
            return r.pass_()
        missed = [i for i, c in enumerate(clients[1:], 1) if msg not in c.buffer]
        return r.fail(r.expected, f"clients missing message: {missed}")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        for c in clients:
            c.close()


@register("56. MULTI - KICK broadcast seen by every member")
def t():
    r = Result("56")
    r.expected = "KICK broadcast to every member"
    clients = []
    try:
        ch = "#" + uniq("c")
        for _ in range(4):
            c, _ = new_client()
            clients.append(c)
        for c in clients:
            c.send(f"JOIN {ch}"); c.wait_for("366", 2.0)
        time.sleep(0.3)
        for c in clients:
            c.clear()
        victim = clients[-1].nick
        clients[0].send(f"KICK {ch} {victim} :goodbye")
        time.sleep(0.5)
        ok = all(c.wait_for("KICK", timeout=2.0) for c in clients)
        if ok:
            return r.pass_()
        missed = [i for i, c in enumerate(clients) if "KICK" not in c.buffer]
        return r.fail(r.expected, f"clients missing KICK: {missed}")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        for c in clients:
            c.close()


@register("57. MULTI - nickname freed after client disconnect (no QUIT command)")
def t():
    # There's no QUIT handler and disconnect() never broadcasts anything
    # to channel peers — leave_chanels() just silently removes fd from
    # member/operator/invite lists. The only externally observable proof
    # that cleanup happened is that a *new* connection can immediately
    # reuse the nickname the old client held, which only works if
    # Server::disconnect() actually erased the old Client entry.
    r = Result("57")
    r.expected = "second client can register with the freed nickname"
    c1 = c2 = None
    try:
        c1, n1 = new_client()
        ch = "#" + uniq("c")
        c1.send(f"JOIN {ch}"); c1.wait_for("366", 2.0)
        c1.close()
        time.sleep(0.3)
        c2 = IrcClient()
        if login(c2, n1):
            return r.pass_()
        return r.fail(r.expected, c2.buffer or "(no response)")
    except Exception as e:
        return r.fail(r.expected, "", str(e))
    finally:
        if c1: c1.close()
        if c2: c2.close()


# ===========================================================================
# Runner
# ===========================================================================
def truncate(s, n=500):
    s = s.replace("\r", "").strip()
    if len(s) <= n:
        return s
    return s[:n] + f"\n... [{len(s) - n} more chars]"


def show_diff(expected, actual):
    exp_lines = [expected] if isinstance(expected, str) else list(expected)
    act_lines = [actual] if isinstance(actual, str) else list(actual)
    diff = difflib.unified_diff(
        exp_lines, act_lines,
        fromfile="expected", tofile="actual", lineterm="",
    )
    printed = False
    for line in diff:
        printed = True
        if line.startswith("+"):
            print(f"    {C.OK}{line}{C.END}")
        elif line.startswith("-"):
            print(f"    {C.FAIL}{line}{C.END}")
        else:
            print(f"    {C.DIM}{line}{C.END}")
    if not printed:
        print(f"    {C.DIM}(no textual diff){C.END}")


def run():
    print(f"{C.BOLD}{C.BLUE}======================================================{C.END}")
    print(f"{C.BOLD}{C.BLUE}       ft_irc - Mandatory Commands Test Suite         {C.END}")
    print(f"{C.BOLD}{C.BLUE}======================================================{C.END}")
    print(f"{C.DIM}server   : {HOST}:{PORT}{C.END}")
    print(f"{C.DIM}password : {PASSWORD}{C.END}")
    print(f"{C.DIM}tests    : {len(TESTS)}{C.END}\n")

    passed = 0
    failures = []

    for name, fn in TESTS:
        try:
            res = fn()
        except Exception as e:
            res = Result(name).fail("no exception", f"exception: {e}", str(e))
        if res.ok:
            print(f"{C.OK}[PASS]{C.END} {name}")
            passed += 1
        else:
            print(f"{C.FAIL}[FAIL]{C.END} {name}")
            failures.append((name, res))

    total = len(TESTS)
    failed = total - passed

    print()
    print(f"{C.BOLD}{C.BLUE}======================================================{C.END}")
    bar_len = 40
    filled = int(bar_len * passed / total) if total else 0
    bar = f"{C.OK}{'#' * filled}{C.FAIL}{'.' * (bar_len - filled)}{C.END}"
    print(f"  {bar}  {C.BOLD}{passed}/{total}{C.END}")

    if failed == 0:
        print(f"  {C.OK}{C.BOLD}*** ALL TESTS PASSED ***{C.END}")
    else:
        print(f"  {C.OK}PASSED: {passed}{C.END}   {C.FAIL}FAILED: {failed}{C.END}")

    if failures:
        print()
        print(f"{C.BOLD}{C.WARN}---- Failure details ----{C.END}")
        for name, res in failures:
            print()
            print(f"{C.FAIL}{C.BOLD}>> {name}{C.END}")
            if res.error:
                print(f"  {C.WARN}error:{C.END} {res.error}")
            print(f"  {C.BLUE}expected:{C.END}")
            for line in truncate(str(res.expected)).splitlines():
                print(f"      {line}")
            print(f"  {C.BLUE}actual:{C.END}")
            for line in truncate(str(res.actual)).splitlines():
                print(f"      {line}")
            print(f"  {C.BLUE}diff:{C.END}")
            show_diff(str(res.expected), str(res.actual))

    print()
    print(f"{C.BOLD}{C.BLUE}======================================================{C.END}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    run()