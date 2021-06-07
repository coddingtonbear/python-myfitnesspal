import getpass

import keyring

KEYRING_SYSTEM = "python-myfitnesspal://myfitnesspal-password"


class NoStoredPasswordAvailable(Exception):
    pass


def get_password_from_keyring(username: str) -> str:
    result = keyring.get_password(KEYRING_SYSTEM, username)
    if result is None:
        raise NoStoredPasswordAvailable(
            "No MyFitnessPal password for {username} could be found "
            "in the system keychain.  Use the `store-password` "
            "command-line command for storing a password for this "
            "username.".format(
                username=username,
            )
        )

    return result


def store_password_in_keyring(username: str, password: str) -> None:
    return keyring.set_password(KEYRING_SYSTEM, username, password)


def delete_password_in_keyring(username: str) -> None:
    return keyring.delete_password(KEYRING_SYSTEM, username)


def get_password_from_keyring_or_interactive(username: str) -> str:
    try:
        return get_password_from_keyring(username)
    except NoStoredPasswordAvailable:
        return getpass.getpass(f"MyFitnessPal password for {username}: ")
