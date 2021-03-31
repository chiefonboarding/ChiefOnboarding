import Vue from 'vue'
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faFile, faFolder, faCheckCircle, faCircle, faBookmark, faQuestionCircle } from '@fortawesome/fontawesome-free-regular'
import { faCertificate, faBars, faTimes, faPlusCircle, faEnvelope, faPhoneSquare } from '@fortawesome/fontawesome-free-solid'
import { faLinkedin, faFacebook, faTwitter } from '@fortawesome/fontawesome-free-brands'

library.add(faFile, faFolder, faCheckCircle, faCircle, faBookmark, faQuestionCircle, faCertificate, faBars, faTimes, faPlusCircle, faEnvelope, faPhoneSquare, faFacebook, faTwitter, faLinkedin)

Vue.component('font-awesome-icon', FontAwesomeIcon)
