// let chapters_from_html = JSON.parse(document.getElementById('chapters').textContent)

var app = new Vue({
  el: '#app',
  delimiters: ['[[', ']]'],
  data: function () {
    return {
      manifest: {
        "form": [],
        "execute": [],
        "exists": {
          "url": "",
          "method": "",
          "expected": "",
          "headers": [],
          "fail_when_4xx_response_code": true
        },
        "revoke": [],
        "headers": [],
        "extra_user_info": [],
        "initial_data_form": [],
        "post_execute_notification": [],
        "results_from": "" // removed
      },
      extra_fields: [], // new hire
      extra_args: [], // integration
      user_id: -1
    }
  },
  mounted () {
    if (document.getElementById('manifest') !== undefined){
      this.manifest = JSON.parse(document.getElementById('manifest').textContent)
    }
  },
  methods: {
    addFormItem () {
      this.manifest.form.push(
        {
          "id": "",
          "url": "",
          "method": "",
          "name": "",
          "type": "",
          "method": "",
          "data_from": "",
          "choice_name": "name",
          "choice_value": "id",
          "items": [],
          "headers": []
        }
      )
    },
    addFormItemsItem (items) {
      items.push(
        {
          "id": "",
          "name": ""
        }
      )
    },
    addNameDescrItem (items) {
      items.push(
        {
          "id": "",
          "name": "",
          "description": ""
        }
      )
    },
    addKeyValueItem (items) {
      items.push(
        {
          "key": "",
          "value": ""
        }
      )
      // force update
      this.manifest.execute.splice(0, 0)
    },
    addRequestItem (arr) {
      arr.push(
        {
          "url": "",
          "method": "",
          "data": "{}",
          "headers": [],
          "cast_data_to_json": false
        }
      )
    },
    toggleStoreData (ex) {
      if (!ex.hasOwnProperty("store_data")) {
        ex.store_data = []
      } else {
        delete ex.store_data
      }
      // force update
      this.manifest.execute.splice(0, 0)
    },
    togglePolling (ex) {
      if (!ex.hasOwnProperty("polling")) {
        ex.polling = {"interval": 5, "amount": 60}
      } else {
        delete ex.polling
      }
      // force update
      this.manifest.execute.splice(0, 0)
    },
    toggleContinueIf (ex) {
      if (!ex.hasOwnProperty("continue_if")) {
        ex.continue_if = {"response_notation": "", "value": ""}
      } else {
        delete ex.continue_if
      }
      // force update
      this.manifest.execute.splice(0, 0)
    },
    toggleSaveAsFile (ex) {
      if (!ex.hasOwnProperty("save_as_file")) {
        ex.save_as_file = ""
      } else {
        delete ex.save_as_file
      }
      // force update
      this.manifest.execute.splice(0, 0)
    },
    removeFormItem (index) {
      this.manifest.form.splice(index, 1)
    },
    removeItemsItem (items, index) {
      items.splice(index, 1)
      // force update
      this.manifest.execute.splice(0, 0)
    },
    removeObjFromList (items, key) {
      items.splice(key, 1)
      // force update
      this.manifest.execute.splice(0, 0)
    },
  }
})
