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
        "oauth": {},
        "extra_user_info": {},
        "initial_data_form": {},
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
      console.log(document.getElementById('manifest').textContent)
      this.manifest = JSON.parse(document.getElementById('manifest').textContent)
      console.log(this.manifest)
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
    },
    removeFormItem (index) {
      this.manifest.form.splice(index, 1)
    },
    removeItemsItem (items, index) {
      items.splice(index, 1)
    },
    removeObjFromList (items, key) {
      items.splice(key, 1)
    },
  }
})
