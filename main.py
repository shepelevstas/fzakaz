import datetime
from enum import Enum
from fastapi import FastAPI, HTTPException, Depends

from pydantic import BaseModel, Field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from withfastapi.db import SessionDep, Album, Session, async_session  #, session, albumTable


app = FastAPI()


class AlbumForm(BaseModel):
  session_id: int = Field(gt=0)
  sh: str = Field(max_length=3)
  shyear: int = Field(ge=1, le=11)
  group: str = Field(max_length=16)


# @app.get('/')
# def home():
#   # raise HTTPException(status_code=403, detail='no root endpoint')
#   return "hi there!"


class ModelName(str, Enum):
  albums = "albums"
  sessions = "sessions"
  pricelists = "pricelists"

modelMap = {
  ModelName.albums: Album,
  ModelName.sessions: Session,
}


@app.get('/{model_name}')
async def albums(model_name: ModelName, session: SessionDep):
  print(f'[ALBUMS] {session=}')
  print(f'[MODEL], {model_name=}, {(model_name == ModelName.albums)=}')

  model = modelMap[model_name]

  data = await session.execute(select(model))
  albums = data.scalars().all()

  return albums


@app.get('/albums/{album_id}')
def album(album_id:int):
  return next((i for i in {} if i['id'] == album_id), {})


@app.post('/albums')
async def create_album(data: AlbumForm, session: SessionDep):
  # now = datetime.datetime.now()

  album = Album(**data.dict())

  session.add(album)
  await session.commit()
  await session.refresh(album)

  # print('[session]', session)
  print(f'[ALBUM] {album=}')

  return {
    'status': 'OK',
    'album': album,
  }


if __name__ == '__main__':
  import uvicorn

  # uvicorn.run('main:app', reload=True)
  uvicorn.run('main:app')
