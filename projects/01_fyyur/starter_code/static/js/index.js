import Datepicker from '../node_modules/vanillajs-datepicker/js/Datepicker.js';

console.log("This is the index.js file");


console.log("Datepicker", Datepicker);

const elem = document.getElementById('datepicker');
console.log("elem", elem);
// const elem = document.querySelector('input[id="datepicker"]');
const datepicker = new Datepicker(elem, {
  showOnClick: true,
  maxNumberOfDates: 100,
}); 
console.log("datepicker", datepicker);

// const elemInline = document.getElementById('datepicker-inline',{});
// console.log("elemInline", elemInline);
// // const elem = document.querySelector('input[id="datepicker"]');
// const datepickerInline = new Datepicker(elemInline, {
//   maxNumberOfDates: 100,
// }); 
// console.log("datepicker-inline", datepickerInline);