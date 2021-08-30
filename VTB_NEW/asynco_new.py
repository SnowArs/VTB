import asyncio
from vtb_processing import vtb
from ib_processing import ib
from fridom_processing import fridom


async def main():
    taskA = loop.create_task(vtb('VTB'))
    taskB = loop.create_task(ib('IB'))
    taskC = loop.create_task(fridom('FRIDOM'))
    await asyncio.wait([taskA, taskB, taskC])


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass

# async def main():
#     taskA = asyncio.create_task(vtb())
#     await taskA
#
# asyncio.run(main())