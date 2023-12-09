class UploadQue {
  fileSymbol = Symbol('file')
  requestSymbol = Symbol('request')
  statusSymbol = Symbol('status')

  constructor(options={}) {
    this.options = options
    this.formAdditionalFields = options['formAdditionalFields']||{}
    this.formEnctype = options['formEnctype']||'multipart/form-data'
    this.formFilefieldName = options['formFilefieldName']||'file'
    this.onProgress = options['progress'] || options['onProgress']
    this.onLoad = options['load'] || options['onLoad']
    this.onError = options['error'] || options['onError']
    this.onAbort = options['abort'] || options['onAbort']
    this.onAborted = options['aborted'] || options['onAborted']
    this.uploadUrl = options['url'] || options['uploadUrl']
    this.onAdd = options['add'] || options['onAdd']
    this.onDeleted = options['onDeleted']
    this.onStatusChange = options['statuschange'] || options['onStatusChange']
    this.onStop = options['onStop']
    this.onResume = options['onResume']
    this.stopClick = options['stop']
    this.resumeClick = options['resume']
    this.deleteClick = options['delete']
    this.renderItem = options['renderItem']
    this.que = []
  }

  addFiles(files, moreFormFields) {
    const item = {
      files: Array.from(files),
      [this.statusSymbol]: 'new',
      status: 'new',
      uploadQue: this,
      done: 0,
    }
    if (moreFormFields) {
      item.moreFormFields = moreFormFields
    }
    this.que.push(item)
    if (this.onAdd) {this.onAdd(item)}
    if (this.renderItem) {item.element = this.renderItem(item)}
    if (item.element) {
      const progress = item.element.querySelector('[data-upq-progress]')
      const stop_resume = item.element.querySelector('[data-upq-btn="stop_resume"]')
      const del = item.element.querySelector('[data-upq-btn="delete"]')

      if (progress) {item.progressElement = progress}
      if (stop_resume) {
        item.stopResumeElement = stop_resume
        stop_resume.addEventListener('click', e => {
          if (['new', 'uploading'].includes(item[this.statusSymbol])) {
            if (this.stopClick) {this.stopClick(item, e)}
            this.stop(item)
          } else if (['abort', 'aborted', 'error'].includes(item[this.statusSymbol])) {
            if (this.resumeClick) {this.resumeClick(item, e)}
            this.resume(item)
          }
        })
      }
      if (del) {
        item.deleteElement = del
        del.addEventListener('click', e => {
          if (this.deleteClick) {
            this.deleteClick(item, e)
          }
          this.delete(item)
        })
      }
    }
    this.step()
  }

  add(file, moreFormFields) {
    const item = {
      file,
      [this.fileSymbol]: file,
      [this.statusSymbol]: 'new',
      status: 'new',
      uploadQue: this,
      done: 0,
    }
    item.name = file.name
    if (moreFormFields) {
      item.moreFormFields = moreFormFields
    }
    this.que.push(item)
    if (this.onAdd) {this.onAdd(item)}
    if (this.renderItem) {item.element = this.renderItem(item)}
    if (item.element) {
      const progress = item.element.querySelector('[data-upq-progress]')
      if (progress) {item.progressElement = progress}

      const stop_resume = item.element.querySelector('[data-upq-btn="stop_resume"]')
      if (stop_resume) {
        item.stopResumeElement = stop_resume
        stop_resume.addEventListener('click', e => {
          if (['new', 'uploading'].includes(item[this.statusSymbol])) {
            if (this.stopClick) {this.stopClick(item, e)}
            this.stop(item)
          } else if (['abort', 'aborted', 'error'].includes(item[this.statusSymbol])) {
            if (this.resumeClick) {this.resumeClick(item, e)}
            this.resume(item)
          }
        })
      }

      const del = item.element.querySelector('[data-upq-btn="delete"]')
      if (del) {
        item.deleteElement = del
        del.addEventListener('click', e => {
          if (this.deleteClick) {
            this.deleteClick(item, e)
          }
          this.delete(item)
        })
      }
    }

    this.step()
  }

  step() {
    if (!this.que.length) {
      console.log('que is empty')
      return
    }
    if (this.que.some(i => i[this.statusSymbol] == 'uploading')) {
      console.log('already uploading')
      return
    }
    const item = this.que.find(i => i[this.statusSymbol] == 'new')
    if (!item) {
      console.log('no new items')
      return
    }
    console.log('upload!')
    this.upload(item)
  }

  next() {
    this.step()
  }

  setStatus(item, value) {
    if (this.onStatusChange) {
      this.onStatusChange(item, value, item[this.statusSymbol])
    }
    item[this.statusSymbol] = value
    item.status = value
  }

  count_done() {
    return this.que.filter(item=>item[this.statusSymbol]=='done').length
  }

  cur_item() {
    return this.que.find(item=>item[this.statusSymbol]=='uploading')
  }

  upload(item) {
    this.setStatus(item, 'uploading')
    const form = new FormData()
    form.enctype = this.formEnctype
    for (let k in this.formAdditionalFields) {
      form.set(k, this.formAdditionalFields[k])
    }

    if (this.fileSymbol in item) {
      console.log('upload one file')
      form.set(this.formFilefieldName, item[this.fileSymbol])
    } else if ('files' in item) {
      console.log('upload many files')
      Array.from(item.files).forEach(file => {
        form.append(this.formFilefieldName, file)
      })
    }

    if (item.moreFormFields) {
      for (let k in item.moreFormFields) {
        form.set(k, item.moreFormFields[k])
      }
    }

    const req = new XMLHttpRequest()
    item[this.requestSymbol] = req

    req.upload.addEventListener('progress', e => {
      const value = Math.round(e.loaded/e.total*1000)/10
      item.done = value

      if (
        (!this.onProgress || !this.onProgress(item, e))
        && item.progressElement
      ) {
        item.progressElement.innerText = `${value}%`
      }
    })

    req.addEventListener('load', e => {
      this.setStatus(item, 'done')
      if (this.onLoad) {this.onLoad(item, e)}
      this.step()
    })

    req.addEventListener('error', e => {
      this.setStatus(item, 'error')
      if (this.onError) {this.onError(item, e)}
      this.step()
    })

    req.addEventListener('abort', e => {
      this.setStatus(item, 'aborted')
      if (this.onAborted) {this.onAborted(item, e)}
      this.step()
    })

    req.open('POST', this.uploadUrl)
    req.send(form)
  }

  abort(item) {
    if (this.onStop) {this.onStop(item)}
    if (item[this.statusSymbol] == 'uploading' && item[this.requestSymbol]) {
      if (this.onAbort) {this.onAbort(item)}
      item[this.requestSymbol].abort()
    }
  }

  stop(item) {
    this.abort(item)
  }

  resume(item) {
    if (this.onResume) {this.onResume(item)}
    if (item[this.statusSymbol] == 'done') {return}
    if (item[this.statusSymbol] == 'uploading') {return}
    item.done = 0
    this.setStatus(item, 'new')
    this.step()
  }

  delete(item) {
    this.abort(item)
    this.que = this.que.filter(i => i != item)
    if (this.onDeleted) {
      this.onDeleted(item)
    }
  }
}
