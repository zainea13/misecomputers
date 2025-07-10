"use strict"
// grab items from page
const swiperWindow = document.querySelector('.swiper-window');
const wrapper = document.querySelector('.swiper-wrapper');
const thumbnails = document.querySelectorAll('.thumbnail');

// Adjust position of the "out of stock banner"
const banner = document.querySelector('.over-image');

// Get dimensions
const bannerHeight = banner.offsetHeight;
const swiperWidth = swiperWindow.offsetWidth;
const swiperHeight = swiperWindow.offsetHeight;

function bannerPosition() {
    // banner.style.width = `${swiperWidth/2}px`;
    banner.style.left = `${(swiperWidth - (swiperWidth/2)) / 2}px`;
}
bannerPosition();
window.addEventListener('resize', bannerPosition);


console.log(banner)



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