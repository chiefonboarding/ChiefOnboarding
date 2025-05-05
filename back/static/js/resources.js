function initResource() {
  var currentData = {};
  var editor = undefined;
  function initEditor(data) {
    editor = new EditorJS({
      minHeight: 30,
      holder: 'element',
      placeholder: placeholder,
      data: data,
      tools: {
        header: Header,
        quote: Quote,
        list: {
          class: NestedList,
          inlineToolbar: true,
        },
        embed: {
          class: Embed,
          inlineToolbar: false,
          config: {
            services: {
              youtube: true,
            }
          }
        },
        delimiter: Delimiter,
        image: {
          class: ImageTool,
          config: {
            uploader: {
              /**
               * Upload file to the server and return an uploaded image data
               * @param {File} file - file selected from the device or pasted by drag-n-drop
               * @return {Promise.<{success, file: {url}}>}
               */
              async uploadByFile(file){
                // your own uploading logic here
                let response = await getSignedURL(file)
                let completed = await uploadFile(file, response)
                response["file"]["url"] = response["file"]["get_url"]
                return response
              },
            }
          }
        },
        attaches: {
          class: AttachesTool,
          config: {
            uploader: {
              /**
               * Upload file to the server and return an uploaded image data
               * @param {File} file - file selected from the device or pasted by drag-n-drop
               * @return {Promise.<{success, file: {url}}>}
               */
              async uploadByFile(file){
                // your own uploading logic here
                let response = await getSignedURL(file)
                let completed = await uploadFile(file, response)
                return response
              },
            }
          }
        }
      },
      onChange: function (value) {
        value.saver.save().then(function(data) {
          app.saveData(data)
        })
      }
    });
  }

  Vue.component('v-node', {
    template: '#v-node',
    delimiters: ['[[', ']]'],
    props: {
      chapter: Object,
      currentItem: Object,
    },
    methods: {
      changeChapter (chapter) {
        app.chapter = chapter
        editor.destroy()
        initEditor(app.chapter.content)
      },
      move (item, upOrDown) {
        app.findParent(app.chapters, item.id)
        const oldIndex = app.parent.findIndex(a => a.id === item.id)
        // check if new index exists
        if ((oldIndex + 1 === app.parent.length && upOrDown === 1) || (oldIndex === 0 && upOrDown === -1)) { return }
        app.parent.splice(oldIndex, 1)
        app.parent.splice(oldIndex + upOrDown, 0, item)
      },
      add (item, contentType) {
        app.findParent(app.chapters, item.id)
        const index = app.parent.findIndex(a => a.id === item.id)
        const newItem = {
          id: app.getRandomString(),
          type: contentType,
          name: newItemText,
          content: { blocks: [] },
          parent_chapter: null,
          children: []
        }
        if (contentType === 1) {
          newItem.children = [{
            id: app.getRandomString(),
            type: 0,
            name: newItemText,
            content: {},
            children: [],
            parent_chapter: -1
          }]
        }
        app.parent.splice(index + 1, 0, newItem)
      },
      deleteItem (item) {
        app.findParent(app.chapters, item.id)
        if (app.parent.length === 1) {
          // can't delete last item
          return
        }
        const indexAt = app.parent.findIndex(a => a.id === item.id)
        app.parent.splice(indexAt, 1)
      },
    }
  });

  let chapters_from_html = JSON.parse(document.getElementById('chapters').textContent)

  console.log(chapters_from_html)
  var app = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: function () {
      return {
        chapters: [],
        chapter: { content: [] },
        parent: undefined,
        isImporting: false
      }
    },
    mounted () {
      this.chapters = chapters_from_html
      if (!this.chapters.length) {
        this.chapters = [{
          id: this.getRandomString(),
          type: 0,
          name: newItemText,
          content: { blocks: [] },
          parent_chapter: null,
          children: []
        }]
      }
      this.chapter = this.chapters[0]
      initEditor(this.chapter.content)
    },
    methods: {
      saveData (data) {
        this.chapter.content = data
      },
      findParent (source, id) {
        // https://stackoverflow.com/a/23460304
        if (id === undefined) {
          this.parent = null
          return
        }
        let key
        for (key in source) {
          const item = source[key]
          if (item.id === id) {
            this.parent = source
            return
          }
          if (item.children) {
            const subresult = this.findParent(item.children, id)
            if (subresult) {
              this.parent = item.children
              return
            }
          }
        }
        return null
      },
      addQuestion () {
        const uniqueId = this.getRandomString()
        this.chapter.content.blocks.push({
          'content': "",
          'items': [{ 'id': uniqueId, 'text': '' }],
          'type': 'question',
          'answer': uniqueId
        })
      },
      addOption (items) {
        items.push({ 'text': '', 'id': this.getRandomString() })
      },
      removeQuestion (index) {
        this.chapter.content.blocks.splice(index, 1)
      },
      removeOption (indexQuestion, indexOption) {
        this.chapter.content.blocks[indexQuestion].items.splice(indexOption, 1)
      },
      getRandomString () {
        // from https://stackoverflow.com/a/6860916
        return "temp-" + (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1)
      },
      importQuestionsFromPDF() {
        // Create a file input element
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'application/pdf';
        fileInput.style.display = 'none';
        document.body.appendChild(fileInput);

        // Handle file selection
        fileInput.addEventListener('change', async (event) => {
          if (event.target.files.length > 0) {
            const file = event.target.files[0];

            // Check file size (limit to 10MB)
            if (file.size > 10 * 1024 * 1024) {
              alert('File is too large. Please select a PDF smaller than 10MB.');
              document.body.removeChild(fileInput);
              return;
            }

            // Create form data
            const formData = new FormData();
            formData.append('pdf_file', file);

            // Show loading state
            this.isImporting = true;

            try {
              // Get CSRF token
              const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

              // Send the PDF to the server
              const response = await fetch('/api/pdf-extract-questions/', {
                method: 'POST',
                body: formData,
                headers: {
                  'X-CSRFToken': csrfToken,
                },
              });

              if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to process PDF');
              }

              const data = await response.json();

              // Add the extracted questions to the current chapter
              if (data.questions && data.questions.length > 0) {
                // If the chapter doesn't have a content.blocks array, initialize it
                if (!this.chapter.content.blocks) {
                  this.chapter.content.blocks = [];
                }

                // Add each question to the chapter
                data.questions.forEach(question => {
                  this.chapter.content.blocks.push(question);
                });

                alert(`Successfully imported ${data.questions.length} questions from the PDF.`);
              } else {
                alert('No questions were found in the PDF. Try a different file or generate questions with AI instead.');
              }
            } catch (error) {
              console.error('Error importing questions:', error);
              alert(`Failed to import questions: ${error.message || 'Unknown error'}`);
            } finally {
              this.isImporting = false;
              document.body.removeChild(fileInput);
            }
          }
        });

        // Trigger the file input click
        fileInput.click();
      }
    }
  })
}
// FOR RESOURCE/COURSE
$(document).on('change', "#id_course", function() {
  if (this.checked == true){
    $("#div_id_on_day").parent().removeClass("d-none")
    $("#div_id_remove_on_complete").parent().parent().removeClass("d-none")
  } else {
    $("#div_id_on_day").parent().addClass("d-none")
    $("#div_id_remove_on_complete").parent().parent().addClass("d-none")
  }
})
