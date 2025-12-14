const sum = list => list.reduce((a, b) => a + b, 0)
function map(fn,list){
  if (list===void 0) return function(list){return map(fn, list)}
  var l = list.length
  if (l===0) return []
  var res = Array(l)
  for (var i=0;i<l;i++)
    res[i] = fn(list[i], i, list)
  return res
}
const compose = f => g => a => f(g(a))
const pipe = (...args) => fold(_pipe, args[0], tail(args))
const pipe2 = f => g => a => g(f(a))
const _pipe = (f,g) => (...args) => g.call(null, f.apply(null, args))
function fold(fn, acc, list){
  if (list===void 0)
    return list => fold(fn, acc, list)
  for (var i = 0, l = list.length; i<l; i++)
    acc = fn(acc, list[i], i, list)
  return acc
}
const tail = list => drop(1, list)
function drop(n,list){
  if (list===void 0)
    return list => drop(n, list)
  if (Array.isArray(list))
    return list.slice(n)
  if (isArrayLike(list)){
    var res = [], i = n<0?list.length-n:n, l = list.length
    while (i<l) res.push(list[i++])
    return res
  }
}
function isArrayLike(a){return a!=null&&typeof(a)=="object"&&a.length>=0}
const product = ([a,b]) => a * b
const apply = a => f => f(a)
const flip = f => b => a => f(a,b)
// : [a->b] -> a -> [b]
const applyFuncs = pipe(flip(map), pipe2(apply))
const type = x => {
    const t = typeof x
    if (t === 'object') {
        if (x === null) return 'null'
        if (Array.isArray(x)) return 'array'
    }
    if (t === 'number' && Number.isNaN(x)) { return 'nan' }
    return t
}
const eq = (a, b) => {
    const ta = type(a)
    const tb = type(b)
    if (ta !== tb) {return false}
    switch (ta) {
        case 'number':
        case 'nan':
        case 'boolean':
        case 'string': {
            return a === b
        }
        case 'array': {
            if (a.length !== b.length) {return false}
            return a.every((aa, index) => eq(aa, b[index]))
        }
        case 'object': {
            const ka = Object.keys(a).sort()
            const kb = Object.keys(b).sort()
            if (ka.length !== kb.length) {return false}
            if (!eq(ka, kb)) {return false}
            return ka.every(k => eq(a[k], b[k]))
        }
    }
    return a == b
}
