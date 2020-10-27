import { Node } from 'tiptap'
import { nodeInputRule } from 'tiptap-commands'

/**
 * Matches following attributes in Markdown-typed image: [, alt, src, title]
 *
 * Example:
 * ![Lorem](image.jpg) -> [, "Lorem", "image.jpg"]
 * ![](image.jpg "Ipsum") -> [, "", "image.jpg", "Ipsum"]
 * ![Lorem](image.jpg "Ipsum") -> [, "Lorem", "image.jpg", "Ipsum"]
 */
const IMAGE_INPUT_REGEX = /!\[(.+|:?)]\((\S+)(?:(?:\s+)["'](\S+)["'])?\)/

export default class File extends Node {
  get name () {
    return 'file'
  }

  get schema () {
    return {
      inline: false,
      attrs: {
        id: -1,
        name: ''
      },
      group: 'block',
      draggable: true,
      parseDOM: [
        {
          tag: 'span',
          getAttrs: (dom) => {
            const id = dom.getAttribute('id')
            const name = dom.textContent
            return { id, name }
          }
        }
      ],
      toDOM: node => [
        'span',
        {
          class: 'mention',
          'id': node.attrs.id
        },
        `${node.attrs.name}`
      ]
    }
  }

  commands ({ type }) {
    return attrs => (state, dispatch) => {
      const { selection } = state
      const position = selection.$cursor ? selection.$cursor.pos : selection.$to.pos
      const node = type.create(attrs)
      const transaction = state.tr.insert(position, node)
      dispatch(transaction)
    }
  }

  inputRules ({ type }) {
    return [
      nodeInputRule(IMAGE_INPUT_REGEX, type, (match) => {
        const [, name, id] = match
        return {
          name,
          id
        }
      })
    ]
  }
}
