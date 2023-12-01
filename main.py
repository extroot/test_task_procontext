import asyncio
import datetime
import xml.etree.ElementTree as ET

import aiohttp
import requests

url = 'http://www.cbr.ru/scripts/XML_daily_eng.asp?date_req={}'


def print_answer(answer: dict[str, tuple[str, list[tuple[float, str]]]]) -> None:
    for key in answer.keys():
        min_val = min(answer[key][1], key=lambda x: x[0])
        max_val = max(answer[key][1], key=lambda x: x[0])
        average = sum([x[0] for x in answer[key][1]]) / len(answer[key][1])
        print(
            f'{key:22} ({answer[key][0]}) – minimum value: {min_val[0]:8.4f} on {min_val[1]};'
            f' maximum value: {max_val[0]:8.4f} on {max_val[1]}; average value: {average:8.4f}'
        )


def sync_solution(start_date, period: int = 90) -> None:
    out: dict[str, tuple[str, list[tuple[float, str]]]] = {}

    for i in range(period):
        start_date += datetime.timedelta(days=1)
        response = requests.get(url.format(start_date.strftime('%d/%m/%Y')))
        data = response.content

        tree = ET.fromstring(data)
        for child in tree:
            if child[3].text not in out.keys():
                out[str(child[3].text)] = (str(child[1].text), [])
            out[str(child[3].text)][1].append((
                float(child[4].text.replace(',', '.')),
                start_date.strftime('%d/%m/%Y')
            ))

    print_answer(out)


async def fetch_data(session, date) -> bytes:
    async with session.get(url.format(date.strftime('%d/%m/%Y'))) as response:
        return await response.read()


async def async_solution(start_date: datetime.date, period: int = 90) -> None:
    out: dict[str, tuple[str, list[tuple[float, str]]]] = {}

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(period):
            current_date = start_date + datetime.timedelta(days=i + 1)
            tasks.append(fetch_data(session, current_date))

        responses = await asyncio.gather(*tasks)

    for i, data in enumerate(responses):
        current_date = start_date + datetime.timedelta(days=i + 1)
        tree = ET.fromstring(data)
        for child in tree:
            key = str(child[3].text)
            if key not in out:
                out[key] = (str(child[1].text), [])
            out[key][1].append((
                float(child[4].text.replace(',', '.')),
                current_date.strftime('%d/%m/%Y')
            ))

    print_answer(out)


if __name__ == '__main__':
    start = datetime.date.today() - datetime.timedelta(days=90)

    # Sync solution, ~time: 15.06 seconds
    # sync_solution(start)

    # Use async solution by default
    # Async solution, ~time: 3.46 seconds
    asyncio.run(async_solution(start))
