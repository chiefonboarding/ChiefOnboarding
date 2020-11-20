<template>
  <v-expansion-panels accordion>
    <v-expansion-panel v-for="(items, _item, index) in value" :key="index" style="-webkit-box-shadow: unset; box-shadow: unset;">
      <v-expansion-panel-header>
        {{ typeOptions[index].name }} ({{ items.length }})
      </v-expansion-panel-header>
      <v-expansion-panel-content
        style="background-color: #f5f5f5 !important;"
      >
        <v-card>
          <v-data-table
            :items="items"
            :item-key="`${typeOptions[index].name}-${index}`"
            :headers="[{ text: 'item', value: 'name' }, { text: 'tags', value: 'tags' }]"
            @click:row="openModal(typeOptions[index], ...arguments)"
            hide-default-footer
            hide-default-header
            disable-pagination
            style="margin-top: 10px;"
          >
            <template v-slot:item.tags="{ item }">
              <div class="text-right">
                <v-chip v-for="(i, _index) in item.tags" :key="'t' + _index" label small>
                  {{ i }}
                </v-chip>
                <span @click.stop="remove(item, typeOptions[index].slug)" class="red-remove">
                  <i style="cursor:pointer; top: 2px;position: relative;" class="far fa-times-circle" />
                </span>
              </div>
            </template>
            <template v-slot:no-data>
              {{ $t('collection.noItemsPicked') }}
            </template>
            <template v-slot:footer>
              <td style="text-align:center; width: 100%;" class="pa-3 pt-1" colspan="2">
                <v-btn @click="setSelectionItems(typeOptions[index])" color="secondary" small>
                  {{ $t('collection.addTemplate') }}
                </v-btn>
                <v-btn @click="openModal(typeOptions[index], {})" color="secondary" small>
                  {{ $t('collection.addNewitem') }}
                </v-btn>
              </td>
            </template>
          </v-data-table>
        </v-card>
      </v-expansion-panel-content>
    </v-expansion-panel>
    <SelectTemplates v-model="showModal" :items="selectionItems" @clickedItem="addItem" />
    <TodoModal v-model="openTodoModal" :to-do="item" @change="changedItem('to_do', ...arguments)" />
    <PreboardingModal v-model="openPreboardingModal" :preboarding="item" @change="changedItem('preboarding', ...arguments)" />
    <ResourceModal v-model="openBookModal" :resource="item" @change="changedItem('resources', ...arguments)" />
    <IntroModal v-model="openIntroModal" :intro="item" @change="changedItem('introductions', ...arguments)" />
    <AppointmentModal v-model="openAppointmentModal" :appointment="item" @change="changedItem('appointments', ...arguments)" />
  </v-expansion-panels>
</template>

<script>
import TodoModal from './TodoModal'
import IntroModal from './IntroModal'
import ResourceModal from './ResourceModal'
import PreboardingModal from './PreboardingModal'
import AppointmentModal from './AppointmentModal'
export default {
  components: { TodoModal, PreboardingModal, IntroModal, AppointmentModal, ResourceModal },
  props: {
    value: {
      type: Object,
      required: true
    },
    errors: {
      type: Object,
      default: () => { return {} }
    }
  },
  data: vm => ({
    collection: [],
    search: '',
    tab: '',
    todos: '',
    showModal: false,
    openPreboardingModal: false,
    openBookModal: false,
    openIntroModal: false,
    openAppointmentModal: false,
    openSequenceModal: false,
    openTodoModal: false,
    item: {},
    templateSelectorChoice: '',
    typeOptions: [
      { name: vm.$t('templates.preboarding'), items: vm.$store.state.preboarding.all, slug: 'preboarding' },
      { name: vm.$t('templates.todos'), items: vm.$store.state.todos.all, slug: 'to_do' },
      { name: vm.$t('templates.resources'), items: vm.$store.state.resources.all, slug: 'resources' },
      { name: vm.$t('templates.intros'), items: vm.$store.state.intros.all, slug: 'introductions' },
      { name: vm.$t('templates.appointments'), items: vm.$store.state.appointments.all, slug: 'appointments' }
    ],
    selectionItems: []
  }),
  computed: {
    errorMessages () {
      return JSON.parse(JSON.stringify(this.errors))
    }
  },
  watch: {
    errors (value) {
      if ('content' in value) {
        this.$store.dispatch('showSnackbar', 'Content: ' + value.content[0])
      }
    }
  },
  methods: {
    setSelectionItems (value) {
      this.selectionItems = value.items
      this.templateSelectorChoice = value.slug
      this.showModal = true
    },
    openModal (option, item) {
      if (option.slug === 'to_do') { this.openTodoModal = true }
      if (option.slug === 'preboarding') { this.openPreboardingModal = true }
      if (option.slug === 'resources') { this.openBookModal = true }
      if (option.slug === 'introductions') { this.openIntroModal = true }
      if (option.slug === 'appointments') { this.openAppointmentModal = true }
      this.item = item
    },
    addItem (value) {
      this.$emit('onAdd', { 'type': this.templateSelectorChoice, 'item': value })
    },
    remove (value, objType) {
      this.value[objType].splice(this.value[objType].findIndex(a => a.id === value.id), 1)
      this.$emit('removeItem', { 'type': objType, 'item': value })
    },
    changedItem (type, value) {
      const tempType = type
      this.value[tempType].splice(this.value[tempType].findIndex(a => a.id === this.item.id), 1)
      this.$emit('onChange', {
        'remove': {
          'type': tempType,
          'item': this.item
        },
        'add': {
          'type': tempType,
          'item': value.add
        }
      })
    }
  }
}
</script>
