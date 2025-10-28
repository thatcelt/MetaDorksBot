from base64 import b64decode
from asyncio import run
from re import findall
from json import dump
from requests import get
from os import mkdir

from typing import (
    Dict,
    Any,
    List
)

from aminodorksfix.asyncfix import (
    Client,
    SubClient
)

print(f"""\033[0;35m
{b64decode("IF9fX19fICAgICBfICAgICAgIF9fX18gICAgICAgICAgXyAgICAgICAKfCAgICAgfF9fX3wgfF8gX19ffCAgICBcIF9fXyBfX198IHxfIF9fXyAKfCB8IHwgfCAtX3wgIF98IC4nfCAgfCAgfCAuIHwgIF98ICdffF8gLXwKfF98X3xffF9fX3xffCB8X18sfF9fX18vfF9fX3xffCB8XyxffF9fX3wKICAgICAgICAgICAgICAgICA=".encode()).decode()}
""")

VARIANTS = [
    "Collect metadata from user",
    "Collect metadata from chat",
    "Collect metadata from community",
    "Collect metadata from blog",
    "Collect metadata from wiki"
]


def colorize(text: str, status: str) -> str:
    return f"\033[0;35m[\033[0m{status}\033[0;35m] \033[0m{text}\033[0;35m"


def build_methods(client: Client, ndc_id: str = None) -> Dict[str, Any]:
    if ndc_id:
        client = SubClient(
            comId=ndc_id,
            profile=client.profile  # pyright: ignore[reportArgumentType]
        )

    methods = {
        "user": client.get_user_info,
        "chat": client.get_chat_thread,
        "community": client.get_community_info,
        "blog": client.get_blog_info,
        "wiki": client.get_wiki_info  # pyright: ignore[reportAttributeAccessIssue]
    }

    return methods


async def login(client: Client) -> None:
    try:
        await client.login(input(colorize("Email: ", "*")), input(colorize("Password: ", "*")))
    except Exception as e:
        print(f"[LoginException]: {e}")
        await login(client)


async def collect_data(client: Client, variant: str) -> None:
    link_data = await client.get_from_code(input(colorize(f"Enter the {variant} link: ", "*")))
    
    json = (await build_methods(
        client=client,
        ndc_id=link_data.comId
    ).get(variant, "user")(link_data.objectId or link_data.comId)).json
    
    await save_data(
        folder=input(colorize("Enter the folder name or skip: ", "*")) or str(link_data.objectId or link_data.comId),  # type: ignore
        payload=json,
        media_list=list(
            set(
                list(
                    map(lambda media: media, findall(r'http://[^\s"{}[\]]*\.(?:jpg|png)', str(json)))
                )
            )
        )
    )


async def save_data(folder: str, payload: Dict[str, Any], media_list: List[str]) -> None:
    try:
        mkdir(folder)
    except FileExistsError:
        ...
    
    with open(f"{folder}/payload.json", "w", encoding="utf-8") as file:
        dump(payload, file, indent=4, ensure_ascii=False)
    
    for media in media_list:
        with open(f"{folder}/{media.split("/")[4]}", "wb") as file:
            file.write(get(media).content)
            print(colorize(f"Downloaded {media}", "+"))
    
    print(colorize(f"Data saved to {folder}", "+"))


async def main():
    client = Client(api_key=input(colorize("API key: ", "*")), socket_enabled=False)

    await login(client)

    while True:
        for index, variant in enumerate(VARIANTS, 1):
            print(f"{index}. {variant}")
        choice = VARIANTS[int(input(colorize("Enter the variant number: ", "*"))) - 1]
        
        await collect_data(
            client=client,
            variant=choice.split(' ')[3]
        )


if __name__ == "__main__":
    run(main())
