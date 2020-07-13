const fs = require('fs')
fs.rename('../back/static/js/index.html', '../back/organization/templates/index.html', function (err) {
  if (err) { throw err }
})
