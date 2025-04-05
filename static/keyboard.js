function keyboard(code) {
  const key = {}
  key.code = code
  key.isDown = false
  key.isUp = true
  key.press = undefined
  key.release = undefined
  //The `downHandler`
  key.downHandler = (event) => {
    if (event.code === key.code) {
      if (key.isUp && key.press) {
        key.press()
      }
      key.isDown = true
      key.isUp = false
      event.preventDefault()
    }
  }

  //The `upHandler`
  key.upHandler = (event) => {
    if (event.code === key.code) {
      if (key.isDown && key.release) {
        key.release()
      }
      key.isDown = false
      key.isUp = true
      event.preventDefault()
    }
  }

  //Attach event listeners
  const downListener = key.downHandler.bind(key)
  const upListener = key.upHandler.bind(key)

  const subscribe = () => {
    window.addEventListener("keydown", downListener, false)
    window.addEventListener("keyup", upListener, false)
  }
  subscribe()

  key.subscribe = subscribe

  // Detach event listeners
  key.unsubscribe = () => {
    window.removeEventListener("keydown", downListener)
    window.removeEventListener("keyup", upListener)
  }

  return key
}