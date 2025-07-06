from datetime import datetime
from withfastapi.db import Album, sync_eng, engine, albumTable, async_session, session
from sqlalchemy import text, insert
import asyncio


# with sync_eng.connect() as conn:
#   # ret = conn.execute(text("select * from foto_album"))
#   # print(ret)
#   # print(ret.all())
#   ret =

async def foo():
  async with engine.connect() as conn:
    res = await conn.execute(text("select * from foto_album"))
    print(res.all())

# asyncio.run(foo())


async def test_insert():

  a = Album(
    created=datetime.now(),
    updated=datetime.now(),
    sh='138',
    shyear=3,
    group='a',
    session_id=2,
  )

  async with async_session() as ses:
    print('1', ses.add(a))
    await ses.commit()
    # print('2', ses.commit())

  return

  with sync_eng.connect() as conn:
    st = text("INSERT INTO foto_album (created, updated, sh, shyear, `group`, session_id) VALUES ('2025-05-29 21:30:00', '2025-05-29 21:30:00', '90', 1, 'b', 2);")

    st = insert(albumTable).values(
      [
        {
          "created": datetime.now(),
          "updated": datetime.now(),
          "sh": "123",
          "shyear": 2,
          "group": "v",
          "session_id": 1,
        },
      ]
    )

    print('[exec]', conn.execute(st))
    print('[commit]', conn.commit())



# test_insert()
asyncio.run(test_insert())
