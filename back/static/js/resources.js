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
        },
        aiContent: {
          class: AITool,
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
      addQuestion (questionType = 'multiple_choice') {
        const uniqueId = this.getRandomString()

        // Base question structure
        let questionObj = {
          'content': "",
          'question_type': questionType,
          'type': 'question',
          'id': uniqueId
        }

        // Add type-specific properties
        this.addQuestionTypeProperties(questionObj, questionType, uniqueId)

        // Add the question to the chapter
        this.chapter.content.blocks.push(questionObj)

        // Force Vue to update the UI
        this.$forceUpdate();

        // Show a toast notification
        this.showToast(`Added new ${questionType.replace('_', ' ')} question`, 'success')
      },

      // Add type-specific properties to a question based on its type
      addQuestionTypeProperties(questionObj, questionType, uniqueId = null) {
        if (questionType === 'multiple_choice') {
          // If changing from another type to multiple choice, initialize items array
          if (!questionObj.items || !Array.isArray(questionObj.items) || questionObj.items.length === 0) {
            const optionId = uniqueId || this.getRandomString()
            questionObj.items = [{ 'id': optionId, 'text': '' }]
            questionObj.answer = optionId
          }
        } else if (questionType === 'file_upload') {
          questionObj.allowed_extensions = '.pdf,.doc,.docx,.txt'
          questionObj.max_file_size = 5 // MB
          questionObj.required = true
          questionObj.validation_message = 'Please upload a valid file'
        } else if (questionType === 'photo_upload') {
          questionObj.allowed_extensions = '.jpg,.jpeg,.png,.gif'
          questionObj.max_file_size = 5 // MB
          questionObj.required = true
          questionObj.validation_message = 'Please upload a valid image'
        } else if (questionType === 'fill_in_blank') {
          questionObj.correct_answer = ''
          questionObj.case_sensitive = false
          questionObj.placeholder = 'Fill in your answer'
          // Add a hint to the content if it's empty
          if (!questionObj.content) {
            questionObj.content = 'The capital of France is XXXX.'
          }
        } else if (questionType === 'free_text') {
          questionObj.min_length = 0
          questionObj.max_length = 1000
          questionObj.placeholder = 'Enter your answer here...'
        } else if (questionType === 'rating_scale') {
          questionObj.min_rating = 1
          questionObj.max_rating = 5
          questionObj.step = 1
          questionObj.show_labels = true
          questionObj.min_label = 'Poor'
          questionObj.max_label = 'Excellent'
        } else if (questionType === 'date_picker') {
          questionObj.min_date = ''  // Optional min date in YYYY-MM-DD format
          questionObj.max_date = ''  // Optional max date in YYYY-MM-DD format
          questionObj.required = true
          questionObj.placeholder = 'Select a date'
        } else if (questionType === 'checkbox_list') {
          // If changing from another type to checkbox list, initialize items array
          if (!questionObj.items || !Array.isArray(questionObj.items) || questionObj.items.length === 0) {
            const optionId = uniqueId || this.getRandomString()
            questionObj.items = [{ 'id': optionId, 'text': '' }]
          }
          questionObj.selected_items = []  // Array to store selected item IDs
          questionObj.min_selections = 0   // Minimum number of selections required
          questionObj.max_selections = 0   // Maximum number of selections allowed (0 = unlimited)
        }

        return questionObj
      },

      // Handle changing a question's type
      changeQuestionType(question, newType) {
        console.log("Changing question type from", question.question_type, "to", newType);
        console.log("Question before:", JSON.stringify(question));

        // Store the question content and ID
        const content = question.content
        const id = question.id

        // Create a temporary copy of the question to work with
        const tempQuestion = { ...question };

        // Remove type-specific properties from the old type
        if (tempQuestion.question_type === 'multiple_choice' || !tempQuestion.question_type) {
          // Keep items and answer for now, will be removed if not needed
          console.log("Removing multiple choice properties if needed");
        } else if (tempQuestion.question_type === 'file_upload' || tempQuestion.question_type === 'photo_upload') {
          console.log("Removing file/photo upload properties");
          delete tempQuestion.allowed_extensions
          delete tempQuestion.max_file_size
          delete tempQuestion.required
          delete tempQuestion.validation_message
        } else if (tempQuestion.question_type === 'fill_in_blank') {
          console.log("Removing fill in blank properties");
          delete tempQuestion.correct_answer
          delete tempQuestion.case_sensitive
          delete tempQuestion.placeholder
        } else if (tempQuestion.question_type === 'free_text') {
          console.log("Removing free text properties");
          delete tempQuestion.min_length
          delete tempQuestion.max_length
          delete tempQuestion.placeholder
        } else if (tempQuestion.question_type === 'rating_scale') {
          console.log("Removing rating scale properties");
          delete tempQuestion.min_rating
          delete tempQuestion.max_rating
          delete tempQuestion.step
          delete tempQuestion.show_labels
          delete tempQuestion.min_label
          delete tempQuestion.max_label
        } else if (tempQuestion.question_type === 'date_picker') {
          console.log("Removing date picker properties");
          delete tempQuestion.min_date
          delete tempQuestion.max_date
          delete tempQuestion.required
          delete tempQuestion.placeholder
        } else if (tempQuestion.question_type === 'checkbox_list') {
          console.log("Removing checkbox list properties");
          // Keep items for now, will be removed if not needed
          delete tempQuestion.selected_items
          delete tempQuestion.min_selections
          delete tempQuestion.max_selections
        }

        // If changing from multiple choice or checkbox list to another type that doesn't use items, remove items
        if ((newType !== 'multiple_choice' && newType !== 'checkbox_list') &&
            (tempQuestion.question_type === 'multiple_choice' || tempQuestion.question_type === 'checkbox_list' || !tempQuestion.question_type)) {
          console.log("Removing items array");
          delete tempQuestion.items
          delete tempQuestion.answer
          delete tempQuestion.selected_items
        }

        // Update the question type
        tempQuestion.question_type = newType

        // Add properties for the new type
        this.addQuestionTypeProperties(tempQuestion, newType)

        // Preserve the question content and ID
        tempQuestion.content = content
        tempQuestion.id = id

        // Force Vue to recognize the change by replacing the entire question object
        // This is necessary to ensure the UI updates correctly
        Object.keys(question).forEach(key => {
          delete question[key];
        });

        Object.keys(tempQuestion).forEach(key => {
          question[key] = tempQuestion[key];
        });

        console.log("Question after:", JSON.stringify(question));

        // Show a toast notification
        this.showToast(`Question type changed to ${newType}`, 'info')

        // Force Vue to update the UI
        this.$forceUpdate();
      },

      // Validate file upload based on question settings
      validateFileUpload(file, allowedExtensions, maxFileSize) {
        // Check file size
        if (file.size > maxFileSize * 1024 * 1024) {
          return {
            valid: false,
            message: `File is too large. Maximum size is ${maxFileSize}MB.`
          }
        }

        // Check file extension
        const fileName = file.name;
        const fileExt = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();
        const allowedExts = allowedExtensions.split(',');

        if (!allowedExts.includes(fileExt)) {
          return {
            valid: false,
            message: `Invalid file type. Allowed types: ${allowedExtensions}`
          }
        }

        return { valid: true }
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
      // Generate an array of ratings for the rating scale preview
      getRatingRange(question) {
        const min = parseInt(question.min_rating) || 1;
        const max = parseInt(question.max_rating) || 5;
        const ratings = [];

        for (let i = min; i <= max; i++) {
          ratings.push(i);
        }

        return ratings;
      },

      // Format the fill-in-blank question preview by highlighting the blank
      formatFillInBlankPreview(text) {
        if (!text) return '';

        // Replace XXXX or [blank] with a styled input placeholder
        const formattedText = text
          .replace(/XXXX/g, '<span class="bg-light border px-4 py-1 rounded">_____</span>')
          .replace(/\[blank\]/g, '<span class="bg-light border px-4 py-1 rounded">_____</span>');

        return formattedText;
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
