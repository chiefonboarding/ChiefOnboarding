<template>
  <div class="editor page">
    <p style="color: #5e5e5e; font-size: 12px">
      Content
    </p>
    <editor-menu-bubble :editor="editor" @hide="hideLinkMenu" v-slot="{ commands, isActive, getMarkAttrs, menu }" class="menububble">
      <div
        :class="{ 'is-active': menu.isActive }"
        :style="`left: ${menu.left}px; bottom: ${menu.bottom}px;`"
        class="menububble"
      >
        <form v-if="linkMenuIsActive" @submit.prevent="setLinkUrl(commands.link, linkUrl)" class="menububble__form">
          <input
            ref="linkInput"
            v-model="linkUrl"
            @keydown.esc="hideLinkMenu"
            class="menububble__input"
            type="text"
            placeholder="https://"
          >
        </form>

        <template v-else>
          <button
            @click="showLinkMenu(getMarkAttrs('link'))"
            :class="{ 'is-active': isActive.link() }"
            class="menububble__button"
          >
            <span>{{ isActive.link() ? 'Update Link' : 'Add Link' }}</span>
          </button>
          <button
            :class="{ 'is-active': isActive.bold() }"
            @click="commands.bold"
            class="menubar__button"
          >
            <icon name="bold">
              <symbol id="icon--bold" view-box="0 0 24 24" style="color: white">
                <path style="transform: scale(0.5,0.5);" d="M17.194 10.962A6.271 6.271 0 0012.844.248H4.3a1.25 1.25 0 000 2.5h1.013a.25.25 0 01.25.25V21a.25.25 0 01-.25.25H4.3a1.25 1.25 0 100 2.5h9.963a6.742 6.742 0 002.93-12.786zm-4.35-8.214a3.762 3.762 0 010 7.523H8.313a.25.25 0 01-.25-.25V3a.25.25 0 01.25-.25zm1.42 18.5H8.313a.25.25 0 01-.25-.25v-7.977a.25.25 0 01.25-.25h5.951a4.239 4.239 0 010 8.477z" />
              </symbol>
            </icon>
          </button>

          <button
            :class="{ 'is-active': isActive.italic() }"
            @click="commands.italic"
            class="menubar__button"
          >
            <icon name="italic">
              <symbol id="icon--italic" view-box="0 0 24 24" style="color: white">
                <path style="transform: scale(0.5,0.5);" d="M22.5.248h-7.637a1.25 1.25 0 000 2.5h1.086a.25.25 0 01.211.384L4.78 21.017a.5.5 0 01-.422.231H1.5a1.25 1.25 0 000 2.5h7.637a1.25 1.25 0 000-2.5H8.051a.25.25 0 01-.211-.384L19.22 2.98a.5.5 0 01.422-.232H22.5a1.25 1.25 0 000-2.5z" />
              </symbol>
            </icon>
          </button>

          <button
            :class="{ 'is-active': isActive.strike() }"
            @click="commands.strike"
            class="menubar__button"
          >
            <icon name="strike">
              <symbol id="icon--strike" view-box="0 0 24 24" style="color: white">
                <path style="transform: scale(0.5,0.5);" d="M23.75 12.952A1.25 1.25 0 0022.5 11.7h-8.936a.492.492 0 01-.282-.09c-.722-.513-1.482-.981-2.218-1.432-2.8-1.715-4.5-2.9-4.5-4.863 0-2.235 2.207-2.569 3.523-2.569a4.54 4.54 0 013.081.764 2.662 2.662 0 01.447 1.99v.3a1.25 1.25 0 102.5 0v-.268a4.887 4.887 0 00-1.165-3.777C13.949.741 12.359.248 10.091.248c-3.658 0-6.023 1.989-6.023 5.069 0 2.773 1.892 4.512 4 5.927a.25.25 0 01-.139.458H1.5a1.25 1.25 0 000 2.5h10.977a.251.251 0 01.159.058 4.339 4.339 0 011.932 3.466c0 3.268-3.426 3.522-4.477 3.522-1.814 0-3.139-.405-3.834-1.173a3.394 3.394 0 01-.65-2.7 1.25 1.25 0 00-2.488-.246A5.76 5.76 0 004.4 21.753c1.2 1.324 3.114 2 5.688 2 4.174 0 6.977-2.42 6.977-6.022a6.059 6.059 0 00-.849-3.147.25.25 0 01.216-.377H22.5a1.25 1.25 0 001.25-1.255z" />
              </symbol>
            </icon>
          </button>

          <button
            :class="{ 'is-active': isActive.underline() }"
            @click="commands.underline"
            class="menubar__button"
          >
            <icon name="underline">
              <symbol id="icon--underline" view-box="0 0 24 24" style="color: white">
                <path style="transform: scale(0.5,0.5);" d="M22.5 21.248h-21a1.25 1.25 0 000 2.5h21a1.25 1.25 0 000-2.5zM1.978 2.748h1.363a.25.25 0 01.25.25v8.523a8.409 8.409 0 0016.818 0V3a.25.25 0 01.25-.25h1.363a1.25 1.25 0 000-2.5H16.3a1.25 1.25 0 000 2.5h1.363a.25.25 0 01.25.25v8.523a5.909 5.909 0 01-11.818 0V3a.25.25 0 01.25-.25H7.7a1.25 1.25 0 100-2.5H1.978a1.25 1.25 0 000 2.5z" />
              </symbol>
            </icon>
          </button>
        </template>
      </div>
    </editor-menu-bubble>

    <editor-floating-menu :editor="editor" v-slot="{ commands, isActive, menu }">
      <div
        :class="{ 'is-active': menu.isActive }"
        :style="`top: ${menu.top}px`"
        class="editor__floating-menu"
      >
        <button
          :class="{ 'is-active': isActive.paragraph() }"
          @click="commands.paragraph"
          class="menubar__button"
        >
          <icon name="paragraph">
            <symbol id="icon--paragraph" view-box="0 0 24 24">
              <path style="transform: scale(0.5,0.5);" d="M22.5.248H7.228a6.977 6.977 0 100 13.954h2.318a.25.25 0 01.25.25V22.5a1.25 1.25 0 002.5 0V3a.25.25 0 01.25-.25h3.682a.25.25 0 01.25.25v19.5a1.25 1.25 0 002.5 0V3a.249.249 0 01.25-.25H22.5a1.25 1.25 0 000-2.5zM9.8 11.452a.25.25 0 01-.25.25H7.228a4.477 4.477 0 110-8.954h2.318A.25.25 0 019.8 3z" />
            </symbol>
          </icon>
        </button>

        <button
          :class="{ 'is-active': isActive.heading({ level: 1 }) }"
          @click="commands.heading({ level: 1 })"
          class="menubar__button"
        >
          H1
        </button>

        <button
          :class="{ 'is-active': isActive.heading({ level: 2 }) }"
          @click="commands.heading({ level: 2 })"
          class="menubar__button"
        >
          H2
        </button>

        <button
          :class="{ 'is-active': isActive.heading({ level: 3 }) }"
          @click="commands.heading({ level: 3 })"
          class="menubar__button"
        >
          H3
        </button>

        <button
          :class="{ 'is-active': isActive.bullet_list() }"
          @click="commands.bullet_list"
          class="menubar__button"
        >
          <icon name="ul">
            <symbol id="icon--ul" view-box="0 0 24 24">
              <circle style="transform: scale(0.5,0.5);" cx="2.5" cy="3.998" r="2.5" /><path style="transform: scale(0.5,0.5);" d="M8.5 5H23a1 1 0 000-2H8.5a1 1 0 000 2z" /><circle style="transform: scale(0.5,0.5);" cx="2.5" cy="11.998" r="2.5" /><path style="transform: scale(0.5,0.5);" d="M23 11H8.5a1 1 0 000 2H23a1 1 0 000-2z" /><circle style="transform: scale(0.5,0.5);" cx="2.5" cy="19.998" r="2.5" /><path style="transform: scale(0.5,0.5);" d="M23 19H8.5a1 1 0 000 2H23a1 1 0 000-2z" />
            </symbol>
          </icon>
        </button>

        <button
          :class="{ 'is-active': isActive.ordered_list() }"
          @click="commands.ordered_list"
          class="menubar__button"
        >
          <icon name="ol">
            <symbol id="icon--ol" view-box="0 0 24 24">
              <path style="transform: scale(0.5,0.5);" d="M7.75 4.5h15a1 1 0 000-2h-15a1 1 0 000 2zm15 6.5h-15a1 1 0 100 2h15a1 1 0 000-2zm0 8.5h-15a1 1 0 000 2h15a1 1 0 000-2zM2.212 17.248a2 2 0 00-1.933 1.484.75.75 0 101.45.386.5.5 0 11.483.63.75.75 0 100 1.5.5.5 0 11-.482.635.75.75 0 10-1.445.4 2 2 0 103.589-1.648.251.251 0 010-.278 2 2 0 00-1.662-3.111zm2.038-6.5a2 2 0 00-4 0 .75.75 0 001.5 0 .5.5 0 011 0 1.031 1.031 0 01-.227.645L.414 14.029A.75.75 0 001 15.248h2.5a.75.75 0 000-1.5h-.419a.249.249 0 01-.195-.406L3.7 12.33a2.544 2.544 0 00.55-1.582zM4 5.248h-.25A.25.25 0 013.5 5V1.623A1.377 1.377 0 002.125.248H1.5a.75.75 0 000 1.5h.25A.25.25 0 012 2v3a.25.25 0 01-.25.25H1.5a.75.75 0 000 1.5H4a.75.75 0 000-1.5z" />
            </symbol>
          </icon>
        </button>
        <button
          :class="{ 'is-active': isActive.image() }"
          @click="$refs.inputFile.click()"
          class="menubar__button"
        >
          <input
            ref="inputFile"
            :accept="['image/jpg', 'image/jpeg', 'image/png']"
            @input="showImagePrompt(commands.image)"
            type="file"
            style="display:none"
          >
          <icon name="image" style="right: 3px;">
            <symbol id="icon--image" view-box="0 0 24 24">
              <circle style="transform: scale(0.5,0.5);" cx="9.75" cy="6.247" r="2.25" /><path style="transform: scale(0.5,0.5);" d="M16.916,8.71A1.027,1.027,0,0,0,16,8.158a1.007,1.007,0,0,0-.892.586L13.55,12.178a.249.249,0,0,1-.422.053l-.82-1.024a1,1,0,0,0-.813-.376,1.007,1.007,0,0,0-.787.426L7.59,15.71A.5.5,0,0,0,8,16.5H20a.5.5,0,0,0,.425-.237.5.5,0,0,0,.022-.486Z" /><path style="transform: scale(0.5,0.5);" d="M22,0H5.5a2,2,0,0,0-2,2V18.5a2,2,0,0,0,2,2H22a2,2,0,0,0,2-2V2A2,2,0,0,0,22,0Zm-.145,18.354a.5.5,0,0,1-.354.146H6a.5.5,0,0,1-.5-.5V2.5A.5.5,0,0,1,6,2H21.5a.5.5,0,0,1,.5.5V18A.5.5,0,0,1,21.855,18.351Z" /><path style="transform: scale(0.5,0.5);" d="M19.5,22H2.5a.5.5,0,0,1-.5-.5V4.5a1,1,0,0,0-2,0V22a2,2,0,0,0,2,2H19.5a1,1,0,0,0,0-2Z" />
            </symbol>
          </icon>
        </button>

        <button
          :class="{ 'is-active': isActive.file() }"
          @click="$refs.fileInput.click()"
          class="menubar__button"
        >
          <input
            ref="fileInput"
            @input="showFilePrompt(commands.file)"
            type="file"
            style="display:none"
          >
          <icon name="file" style="margin-top: -2px; right: 3px;">
            <symbol id="icon--file" view-box="0 0 24 24">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 22 22"><path d="m459 114.75h-420.75c-21.11 0-38.25 17.14-38.25 38.25v420.75c0 21.11 17.14 38.25 38.25 38.25h420.75c21.11 0 38.25-17.14 38.25-38.25v-420.75c0-21.11-17.14-38.25-38.25-38.25m114.75-114.75h-382.5c-21.11 0-38.25 17.14-38.25 38.25v38.25h38.25v-19.12c0-10.557 8.568-19.12 19.12-19.12h344.25c10.557 0 19.12 8.568 19.12 19.12v344.25c0 10.557-8.568 19.12-19.12 19.12h-19.12v38.25h38.25c21.11 0 38.25-17.14 38.25-38.25v-382.5c0-21.11-17.14-38.25-38.25-38.25" transform="matrix(.02614 0 0 .02614 3 2.998)" fill="#4d4d4d" /></svg>
            </symbol>
          </icon>
        </button>

        <button
          :class="{ 'is-active': isActive.blockquote() }"
          @click="commands.blockquote"
          class="menubar__button"
        >
          <icon name="quote">
            <symbol id="icon--quote" view-box="0 0 24 24">
              <path style="transform: scale(0.5,0.5);" d="M18.559 3.932a4.942 4.942 0 100 9.883 4.609 4.609 0 001.115-.141.25.25 0 01.276.368 6.83 6.83 0 01-5.878 3.523 1.25 1.25 0 000 2.5 9.71 9.71 0 009.428-9.95V8.873a4.947 4.947 0 00-4.941-4.941zm-12.323 0a4.942 4.942 0 000 9.883 4.6 4.6 0 001.115-.141.25.25 0 01.277.368 6.83 6.83 0 01-5.878 3.523 1.25 1.25 0 000 2.5 9.711 9.711 0 009.428-9.95V8.873a4.947 4.947 0 00-4.942-4.941z" />
            </symbol>
          </icon>
        </button>

        <button
          @click="commands.horizontal_rule"
          class="menubar__button"
        >
          <icon name="hr">
            <symbol id="icon--hr" view-box="0 0 24 24">
              <path style="transform: scale(0.5,0.5);" d="M5 13a1 1 0 010-2h14a1 1 0 010 2H5z" />
            </symbol>
          </icon>
        </button>
      </div>
    </editor-floating-menu>

    <editor-content :editor="editor" class="editor__content" />

  </div>
</template>

<script>
import {
  Blockquote,
  HardBreak,
  Heading,
  HorizontalRule,
  OrderedList,
  BulletList,
  ListItem,
  Placeholder,
  Bold,
  Code,
  Italic,
  Link,
  Strike,
  Underline
} from 'tiptap-extensions'
import Icon from './EditorIcon' // eslint-disable-line
import Image from './ImageUploader' // eslint-disable-line
import FileUploader from './FileUploader' // eslint-disable-line
import { Editor, EditorContent, EditorMenuBubble, EditorFloatingMenu } from 'tiptap' // eslint-disable-line

export default {
  components: {
    EditorContent,
    EditorMenuBubble,
    EditorFloatingMenu,
    Icon
  },
  props: {
    value: {
      required: true
    }
  },
  data: vm => ({
    editor: new Editor({
      extensions: [
        new Blockquote(),
        new BulletList(),
        new HardBreak(),
        new Heading({ levels: [1, 2, 3] }),
        new HorizontalRule(),
        new ListItem(),
        new OrderedList(),
        new Link(),
        new Bold(),
        new Image(),
        new Code(),
        new FileUploader(),
        new Italic(),
        new Strike(),
        new Underline(),
        new Placeholder({
          emptyNodeText: 'Type...',
          showOnlyWhenEditable: true,
          showOnlyCurrent: true
        })
      ],
      content: ''
    }),
    linkUrl: null,
    content: [],
    linkMenuIsActive: false
  }),
  computed: {
    hasResults () {
      return this.filteredKeywords.length
    },
    showSuggestions () {
      return this.query || this.hasResults
    }
  },
  mounted () {
    this.formatDataToEditorHTML(this.value)
    this.editor.on('update', ({ getJSON }) => {
      // get new content on update
      console.log('updating')
      console.log(getJSON())
      this.$emit('input', this.formatToData(getJSON()))
    })
  },
  beforeDestroy () {
    this.editor.destroy()
  },
  methods: {
    showLinkMenu (attrs) {
      this.linkUrl = attrs.href
      this.linkMenuIsActive = true
      this.$nextTick(() => {
        this.$refs.linkInput.focus()
      })
    },
    hideLinkMenu () {
      this.linkUrl = null
      this.linkMenuIsActive = false
    },
    setLinkUrl (command, url) {
      command({ href: url })
      this.hideLinkMenu()
    },
    showImagePrompt (command) {
      const item = this.$refs.inputFile.files[0]
      this.$org.getPreSignedURL({ name: item.name }).then((data) => {
        this.$org.uploadToAWS(data.url, item).then(() => {
          this.$org.confirmUploaded(data.id).then((fileItem) => {
            const src = fileItem.file_url
            const id = fileItem.id
            command({ src, id })
          })
        })
      })
    },
    showFilePrompt (command) {
      const item = this.$refs.fileInput.files[0]
      this.$org.getPreSignedURL({ name: item.name }).then((data) => {
        this.$org.uploadToAWS(data.url, item).then(() => {
          this.$org.confirmUploaded(data.id).then((fileItem) => {
            const name = fileItem.name
            const id = fileItem.id
            command({ name, id })
          })
        })
      })
    },
    paragraphToHTML (p) {
      let line = ''
      let link = ''
      p.content.forEach((one) => {
        let text = one.text
        if ('marks' in one) {
          if (one.marks.find(a => a.type === 'italic') !== undefined) {
            text = '<i>' + text + '</i>'
          }
          if (one.marks.find(a => a.type === 'code') !== undefined) {
            text = '<code>' + text + '</code>'
          }
          if (one.marks.find(a => a.type === 'bold') !== undefined) {
            text = '<b>' + text + '</b>'
          }
          if (one.marks.find(a => a.type === 'underline') !== undefined) {
            text = '<u>' + text + '</u>'
          }
          if (one.marks.find(a => a.type === 'strike') !== undefined) {
            text = '<strike>' + text + '</strike>'
          }
          if (one.marks.find(a => a.type === 'link') !== undefined) {
            link = one.marks.find(a => a.type === 'link').attrs.href
            text = '<a href="' + link + '">' + text + '</a>'
          }
        }
        line += text
      })
      return line
    },
    lineToHTML (items) {
      let line = ''
      let counter = 0
      items.content.forEach((paragraph) => {
        counter++
        line += this.paragraphToHTML(paragraph)
        if (counter < items.length) {
          line += '<br />'
        }
      })
      return line
    },
    formatToData (content) {
      const newValue = []
      content.content.forEach((one) => {
        if (one.type === 'paragraph') {
          if ('content' in one) {
            newValue.push({
              'type': 'p',
              'content': this.paragraphToHTML(one)
            })
          }
        }
        if (one.type === 'image') {
          if ('attrs' in one) {
            newValue.push({
              'type': 'image',
              'content': '',
              'files': [{ id: one.attrs.id, file_url: one.attrs.src }]
            })
          }
        }
        if (one.type === 'file') {
          if ('attrs' in one) {
            newValue.push({
              'type': 'file',
              'content': '',
              'files': [{ id: one.attrs.id }]
            })
          }
        }
        if (one.type === 'blockquote') {
          if ('content' in one.content[0]) {
            newValue.push({
              'type': 'quote',
              'content': this.lineToHTML(one)
            })
          }
        }
        if (one.type === 'heading') {
          if ('content' in one) {
            newValue.push({
              'type': 'h' + one.attrs.level,
              'content': this.paragraphToHTML(one)
            })
          }
        }
        if (one.type === 'bullet_list' || one.type === 'ordered_list') {
          const listItems = []
          one.content.forEach((item) => {
            if ('content' in item.content[0]) {
              listItems.push({ 'content': this.lineToHTML(item) })
            }
          })
          newValue.push({
            'type': (one.type === 'ordered_list') ? 'ol' : 'ul',
            'items': listItems,
            'content': ''
          })
        }
      })
      return newValue
    },
    formatDataToEditorHTML (value) {
      let html = ''
      console.log(value)
      value.forEach((one) => {
        if (one.type === 'p' && one.content !== '') {
          html += '<p>' + one.content + '</p>'
        }
        if (one.type === 'quote' && one.content !== '') {
          html += '<blockquote>' + one.content + '</blockquote>'
        }
        if (one.type === 'h1' && one.content !== '') {
          html += '<h1>' + one.content + '</h1>'
        }
        if (one.type === 'image') {
          html += '<img src="' + one.files[0].file_url + '" id="' + one.files[0].id + '" alt="' + one.files[0].name + '" />'
        }
        if (one.type === 'file') {
          html += '<span class="mention" id="' + one.files[0].id + '" draggable="true" contenteditable="false">' + one.files[0].name + '</span>'
        }
        if (one.type === 'h2' && one.content !== '') {
          html += '<h2>' + one.content + '</h2>'
        }
        if (one.type === 'h3' && one.content !== '') {
          html += '<h3>' + one.content + '</h3>'
        }
        if ((one.type === 'ul' || one.type === 'ol') && one.items !== []) {
          html += '<' + one.type + '>'
          one.items.forEach((listItem) => {
            html += '<li>' + listItem.content + '</li>'
          })
          html += '</' + one.type + '>'
        }
      })
      this.editor.setContent(html)
    }
  }
}
</script>

<style lang="scss">
$color-black: #000000;
$color-white: #ffffff;
$color-grey: #dddddd;
.menubar__button {
  padding: 3px 8px;
}
.menubar__button:hover {
  background-color: lightgray;
  border-radius: 10px;
}
.menububble.is-active {
    opacity: 1;
    visibility: visible;
}

.menububble {
  position: absolute;
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  z-index: 20;
  background: #000;
  border-radius: 5px;
  padding: .3rem;
  margin-bottom: .5rem;
  -webkit-transform: translateX(-50%);
  transform: translateX(-50%);
  visibility: hidden;
  opacity: 0;
  -webkit-transition: opacity .2s,visibility .2s;
  transition: opacity .2s,visibility .2s;
}
.menububble span {
  color: white;
  padding: 5px;
}
.menububble i:hover {
  cursor: pointer;
  background-color: #CCCCCC;
}
.menububble__input {
  color: white;
}
.editor {
  position: relative;

  &__content {

    overflow-wrap: break-word;
    word-wrap: break-word;
    word-break: break-word;

    * {
      caret-color: currentColor;
    }

    pre {
      padding: 0.7rem 1rem;
      border-radius: 5px;
      background: $color-black;
      color: $color-white;
      font-size: 0.8rem;
      overflow-x: auto;

      code {
        display: block;
      }
    }

    p code {
      padding: 0.2rem 0.4rem;
      border-radius: 5px;
      font-size: 0.8rem;
      font-weight: bold;
      background: rgba($color-black, 0.1);
      color: rgba($color-black, 0.8);
    }

    ul,
    ol {
      padding-left: 1rem;
    }

    li > p,
    li > ol,
    li > ul {
      margin: 0;
    }

    a {
      color: inherit;
    }

    blockquote {
      border-left: 3px solid rgba($color-black, 0.1);
      color: rgba($color-black, 0.8);
      padding-left: 0.8rem;
      font-style: italic;

      p {
        margin: 0;
      }
    }

    img {
      max-width: 100%;
      border-radius: 3px;
    }

    table {
      border-collapse: collapse;
      table-layout: fixed;
      width: 100%;
      margin: 0;
      overflow: hidden;

      td, th {
        min-width: 1em;
        border: 2px solid $color-grey;
        padding: 3px 5px;
        vertical-align: top;
        box-sizing: border-box;
        position: relative;
        > * {
          margin-bottom: 0;
        }
      }

      th {
        font-weight: bold;
        text-align: left;
      }

      .selectedCell:after {
        z-index: 2;
        position: absolute;
        content: "";
        left: 0; right: 0; top: 0; bottom: 0;
        background: rgba(200, 200, 255, 0.4);
        pointer-events: none;
      }

      .column-resize-handle {
        position: absolute;
        right: -2px; top: 0; bottom: 0;
        width: 4px;
        z-index: 20;
        background-color: #adf;
        pointer-events: none;
      }
    }

    .tableWrapper {
      margin: 1em 0;
      overflow-x: auto;
    }

    .resize-cursor {
      cursor: ew-resize;
      cursor: col-resize;
    }

  }
}
.editor, .editor__content, .ProseMirror {
  outline: 0;
}
.editor {
  position: relative;
  border: unset !important;
  &__floating-menu {
    position: absolute;
    z-index: 1;
    margin-top: -0.25rem;
    visibility: hidden;
    opacity: 0;
    transition: opacity 0.2s, visibility 0.2s;
    &.is-active {
      opacity: 1;
      visibility: visible;
    }
  }
}
.mention {
  background: rgba($color-black, 0.1);
  color: rgba($color-black, 0.6);
  font-size: 0.8rem;
  font-weight: bold;
  border-radius: 5px;
  padding: 0.2rem 0.5rem;
  white-space: nowrap;
}
.mention-suggestion {
  color: rgba($color-black, 0.6);
}
.editor p.is-editor-empty:first-child::before {
  content: attr(data-empty-text);
  float: left;
  color: #aaa;
  pointer-events: none;
  height: 0;
  font-style: italic;
}
</style>
