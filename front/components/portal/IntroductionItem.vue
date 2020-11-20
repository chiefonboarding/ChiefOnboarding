<template>
  <div>
    <h3>{{ title }}</h3>
    <v-card
      max-width="344"
      outlined
    >
      <v-img
        v-if="user.profile_image !== null"
        :src="user.profile_image.file_url"
        class="white--text align-end"
        height="200px"
      />
      <v-card-text class="text--primary">
        <h4>{{ user.first_name }} {{ user.last_name }}</h4>

        <div>{{ message }}</div>
        <a v-if="user.linkedin !== ''" :href="user.linkedin | addHTTPS"><font-awesome-icon :icon="['fab', 'linkedin']" style="color: #0077b5 !important" /></a>
        <a v-if="user.facebook !== ''" :href="user.facebook | addHTTPS"><font-awesome-icon :icon="['fab', 'facebook']" style="color: #3b5998 !important" /></a>
        <a v-if="user.twitter !== ''" :href="user.twitter | addHTTPS"><font-awesome-icon :icon="['fab', 'twitter']" style="color: #1da1f2 !important" /></a>
        <a v-if="user.email !== ''" :href="'mailto:' + user.email"><font-awesome-icon :icon="['fas', 'envelope']" style="color: green !important" /></a>
        <a v-if="user.phone !== ''" :href="'tel:' + user.phone"><font-awesome-icon :icon="['fas', 'phone-square']" style="color: gray !important" /></a>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import Mustache from 'mustache'
export default {
  name: 'IntroductionItem',
  props: {
    title: {
      type: String,
      default: ''
    },
    user: {
      type: Object,
      default: () => { return {} }
    },
    disableMustache: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    message () {
      if (this.disableMustache) { return this.user.message }
      return Mustache.render(this.user.message, this.$store.state.baseInfo.new_hire)
    }
  }
}
</script>
