import {
  Node,
  Command,
  nodeInputRule,
  mergeAttributes
} from '@tiptap/core'

declare module '@tiptap/core' {
  interface Commands {
    file: {
      addFile: (options: { name: string, id: number }) => Command,
    }
  }
}

export const inputRegex = /!\[(.+|:?)]\((\S+)(?:(?:\s+)["'](\S+)["'])?\)/
export const File = Node.create({
  name: 'file',

  defaultOptions: {
    inline: false,
    HTMLAttributes: {}
  },

  inline () {
    return this.options.inline
  },

  group () {
    return this.options.inline ? 'inline' : 'block'
  },

  draggable: true,

  addAttributes () {
    return {
      name: {
        default: null
      },
      id: {
        default: null
      },
      disabled: {
        default: true
      },
      class: {
        default: 'file'
      }
    }
  },

  parseHTML () {
    return [
      {
        tag: 'div[name]',
        class: 'file'
      }
    ]
  },

  renderHTML ({ HTMLAttributes }) {
    return ['div', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), HTMLAttributes.name]
  },

  addCommands () {
    return {
      addFile: options => ({ tr, dispatch }) => {
        console.info(options)
        const { selection } = tr
        const node = this.type.create(options)

        if (dispatch) {
          tr.replaceRangeWith(selection.from, selection.to, node)
        }

        return true
      }
    }
  },

  addInputRules () {
    return [
      nodeInputRule(inputRegex, this.type, (match) => {
        const [, id, name] = match

        return { id, name }
      })
    ]
  }
})
