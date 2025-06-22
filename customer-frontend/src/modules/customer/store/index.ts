import { createPinia } from 'pinia';

const pinia = createPinia();

export default pinia;

// Example of a simple store (authStore) - can be moved to its own file e.g. src/store/auth.ts
// import { defineStore } from 'pinia';
// import { ref } from 'vue';

// export const useAuthStore = defineStore('auth', () => {
//   const token = ref<string | null>(localStorage.getItem('authToken'));
//   const user = ref<any | null>(JSON.parse(localStorage.getItem('authUser') || 'null')); // Example, store user object

//   function login(newToken: string, userData: any) {
//     localStorage.setItem('authToken', newToken);
//     localStorage.setItem('authUser', JSON.stringify(userData)); // Store user data
//     token.value = newToken;
//     user.value = userData;
//   }

//   function logout() {
//     localStorage.removeItem('authToken');
//     localStorage.removeItem('authUser');
//     token.value = null;
//     user.value = null;
//   }

//   const isAuthenticated = computed(() => !!token.value);

//   return { token, user, login, logout, isAuthenticated };
// });
```
