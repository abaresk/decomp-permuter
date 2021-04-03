from argparse import ArgumentParser, Namespace
import base64

from nacl.public import SealedBox
from nacl.signing import VerifyKey

from ..core import connect, verify_with_magic
from .base import Command
from .util import ask


class VouchCommand(Command):
    command = "vouch"
    help = "Give someone access to the central server."

    @staticmethod
    def add_arguments(parser: ArgumentParser) -> None:
        parser.add_argument(
            "magic",
            help="Opaque hex string generated by 'setup'.",
        )

    @staticmethod
    def run(args: Namespace) -> None:
        run_vouch(args.magic)


def run_vouch(magic: str) -> None:
    config = connect()

    try:
        vouch_data = base64.b64decode(magic.encode("utf-8"))
        verify_key = VerifyKey(vouch_data[:32])
        signed_nickname = vouch_data[32:]
        msg = verify_with_magic(b"NICK", verify_key, signed_nickname)
        nickname = msg.decode("utf-8")
    except Exception:
        print("Could not parse data!")
        return

    # TODO pre-check (server check to not allow escape codes, e.g.)

    if not ask(f"Grant permuter server access to {nickname}", default=True):
        return

    # TODO send vouch request to server
    # {
    #     "pubkey": config.signing_key.verify_key.encode(),
    #     "vouched_pubkey": verify_key.encode(),
    #     "signed_nickname": signed_nickname,
    # }

    server_address = ":".join(map(str, config.auth_server))
    data = config.auth_verify_key.encode() + server_address.encode("utf-8")
    token = SealedBox(verify_key.to_curve25519_public_key()).encrypt(data)
    print("Granted!")
    print()
    print("Send them the following token:")
    print(base64.b64encode(token).decode("utf-8"))
