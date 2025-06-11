"use strict"
// grab items from page
const swiperWindow = document.querySelector('.swiper-window');
const wrapper = document.querySelector('.swiper-wrapper');
const thumbnails = document.querySelectorAll('.thumbnail');


function imageReveal() {
    // removes active class from all other thumbnails
    thumbnails.forEach((thumbnail) => { 
        thumbnail.classList.remove('active');
    })

    // get data-count
    const i = this.dataset.count;
    // get rem value
    const remValue = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const allImagesWidth = wrapper.scrollWidth + remValue;
    const numberOfImages = thumbnails.length;
    const translateAmount = Math.ceil(allImagesWidth / numberOfImages);
    const amount = ((i * translateAmount)) * -1;
    // add the translate amount
    wrapper.style.translate = `${amount}px`;
    
    // add the active class 
    this.classList.add('active');
}

// add an event listener for the thumbnails
thumbnails.forEach((thumbnail) => { 
    thumbnail.addEventListener('mouseover', imageReveal);
})