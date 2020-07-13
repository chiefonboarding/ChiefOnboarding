<template>
  <v-card
    max-width="344"
    outlined
  >
    <v-img
      v-if="profile_image"
      :src="profile_image"
      class="white--text align-end"
      height="200px"
    />
    <v-container>
      <v-row>
        <v-col cols="12">
          <h3>{{ colleague.full_name }}</h3>
          <p>{{ colleague.position }}</p>
          <a v-if="colleague.linkedin !== ''" :href="colleague.linkedin | addHTTPS"><font-awesome-icon :icon="['fab', 'linkedin']" style="color: #0077b5 !important" /></a>
          <a v-if="colleague.facebook !== ''" :href="colleague.facebook | addHTTPS"><font-awesome-icon :icon="['fab', 'facebook']" style="color: #3b5998 !important" /></a>
          <a v-if="colleague.twitter !== ''" :href="colleague.twitter | addHTTPS"><font-awesome-icon :icon="['fab', 'twitter']" style="color: #1da1f2 !important" /></a>
          <a v-if="colleague.email !== ''" :href="'mailto:' + colleague.email"><font-awesome-icon :icon="['fas', 'envelope']" style="color: green !important" /></a>
          <a v-if="colleague.phone !== ''" :href="'tel:' + colleague.phone"><font-awesome-icon :icon="['fas', 'phone-square']" style="color: gray !important" /></a>
        </v-col>
      </v-row>
    </v-container>
  </v-card>
</template>

<script>
export default {
  name: 'ColleagueItem',
  props: {
    colleague: {
      type: Object,
      required: true
    }
  },
  computed: {
    profile_image () {
      return (this.colleague.profile_image) ? this.colleague.profile_image.file_url : undefined
    }
  }
}
</script>
