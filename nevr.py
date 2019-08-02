from rpm import labelCompare


class NEVR:
    def __init__(self, name: str, epoch: str, version: str, release: str):
        self.name = name
        self.epoch = epoch
        self.version = version
        self.release = release

    @staticmethod
    def from_nevr(nevr: str) -> "NEVR":
        n, ev, r = nevr.rsplit("-", 2)

        if ":" in ev:
            e, v = ev.split(":")
        else:
            e = "0"
            v = ev

        return NEVR(n, e, v, r)

    def __repr__(self) -> str:
        return "NEVR(name={name}, epoch={epoch}, version={version}, release={release}".format(
            name=self.name, epoch=self.epoch, version=self.version, release=self.release
        )

    def __str__(self) -> str:
        return "{name}-{epoch}:{version}-{release}".format(
            name=self.name, epoch=self.epoch, version=self.version, release=self.release
        )

    def __lt__(self, other):
        if not isinstance(other, NEVR):
            return NotImplemented

        if self.name != other.name:
            return NotImplemented

        return labelCompare(
            (self.epoch, self.version, self.release),
            (other.epoch, other.version, other.release)
        ) == -1

    def __gt__(self, other):
        if not isinstance(other, NEVR):
            return NotImplemented

        if self.name != other.name:
            return NotImplemented

        return labelCompare(
            (self.epoch, self.version, self.release),
            (other.epoch, other.version, other.release)
        ) == 1

    def __eq__(self, other):
        if not isinstance(other, NEVR):
            return NotImplemented

        if self.name != other.name:
            return False

        return labelCompare(
            (self.epoch, self.version, self.release),
            (other.epoch, other.version, other.release)
        ) == 0

    def __ne__(self, other):
        if not isinstance(other, NEVR):
            return NotImplemented

        if self.name == other.name:
            return NotImplemented

        return labelCompare(
            (self.epoch, self.version, self.release),
            (other.epoch, other.version, other.release)
        ) != 0

    def __le__(self, other):
        if not isinstance(other, NEVR):
            return NotImplemented

        if self.name != other.name:
            return NotImplemented

        return labelCompare(
            (self.epoch, self.version, self.release),
            (other.epoch, other.version, other.release)
        ) != 1

    def __ge__(self, other):
        if not isinstance(other, NEVR):
            return NotImplemented

        if self.name != other.name:
            return NotImplemented

        return labelCompare(
            (self.epoch, self.version, self.release),
            (other.epoch, other.version, other.release)
        ) != -1

