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
        isImporting: false,
        importStatus: ''
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
      // Helper function to show toast notifications
      showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
          toastContainer = document.createElement('div');
          toastContainer.id = 'toast-container';
          toastContainer.style.position = 'fixed';
          toastContainer.style.top = '20px';
          toastContainer.style.right = '20px';
          toastContainer.style.zIndex = '9999';
          document.body.appendChild(toastContainer);
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast show bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'}`;
        toast.style.minWidth = '300px';
        toast.style.marginBottom = '10px';
        toast.style.color = 'white';
        toast.style.padding = '15px';
        toast.style.borderRadius = '4px';
        toast.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';

        toast.innerHTML = `
          <div class="d-flex">
            <div class="toast-body">
              ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
          </div>
        `;

        // Add close button functionality
        const closeButton = toast.querySelector('.btn-close');
        closeButton.addEventListener('click', () => {
          toastContainer.removeChild(toast);
        });

        // Add toast to container
        toastContainer.appendChild(toast);

        // Auto-remove after 5 seconds for info/success messages
        if (type !== 'error') {
          setTimeout(() => {
            if (toastContainer.contains(toast)) {
              toastContainer.removeChild(toast);
            }
          }, 5000);
        }
      },

      // Update status message in the import button
      updateImportStatus(message) {
        this.importStatus = message;
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
              this.showToast('File is too large. Please select a PDF smaller than 10MB.', 'error');
              document.body.removeChild(fileInput);
              return;
            }

            // Create form data
            const formData = new FormData();
            formData.append('pdf_file', file);

            // Show loading state
            this.isImporting = true;
            this.importStatus = 'Uploading PDF...';
            this.showToast(`Processing PDF: ${file.name}`, 'info');

            try {
              // Get CSRF token
              const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

              // Send the PDF to the server with a longer timeout
              const controller = new AbortController();
              const timeoutId = setTimeout(() => controller.abort(), 180000); // 3 minute timeout

              // Show progress updates
              let progressInterval = setInterval(() => {
                if (this.importStatus === 'Uploading PDF...') {
                  this.updateImportStatus('Extracting text from PDF...');
                } else if (this.importStatus === 'Extracting text from PDF...') {
                  this.updateImportStatus('Generating questions...');
                } else if (this.importStatus === 'Generating questions...') {
                  this.updateImportStatus('Still working...');
                } else if (this.importStatus === 'Still working...') {
                  this.updateImportStatus('Almost there...');
                }
              }, 8000);

              const response = await fetch('/api/pdf-extract-questions/', {
                method: 'POST',
                body: formData,
                headers: {
                  'X-CSRFToken': csrfToken,
                },
                signal: controller.signal
              });

              // Clear the progress interval
              clearInterval(progressInterval);

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

                this.showToast(`Successfully imported ${data.questions.length} questions from the PDF.`, 'success');
              } else {
                this.showToast('No questions were found in the PDF. Try a different file or generate questions with AI instead.', 'error');
              }
            } catch (error) {
              console.error('Error importing questions:', error);

              // Clear the timeout if it exists
              if (timeoutId) clearTimeout(timeoutId);

              // Provide more specific error messages
              if (error.name === 'AbortError') {
                this.showToast('The request timed out. The PDF may be too large or complex. Try a smaller PDF or one with fewer pages.', 'error');
              } else if (error.message && error.message.includes('AI API key not configured')) {
                this.showToast('The AI API key is not configured. Please contact your administrator.', 'error');
              } else {
                this.showToast(`Failed to import questions: ${error.message || 'Unknown error'}`, 'error');
              }
            } finally {
              this.isImporting = false;
              this.importStatus = '';
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
