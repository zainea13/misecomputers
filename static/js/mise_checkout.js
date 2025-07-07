const useShipping = document.querySelector('#use-shipping');
const clearBtn = document.querySelector('.clear-btn');

const shippingForm = document.querySelector('#shipping-info');
const billingForm = document.querySelector('#billing-info');
const creditForm = document.querySelector('#credit-info');
const placeOrderBtn = document.querySelector('#place-order');

const shippingArray = Array.from(shippingForm);
const billingArray = Array.from(billingForm);


// Duplicates the shipping info to the billing info
function copyShippingInput() {
    if (useShipping.checked == true) {
        let counter = 0;
        billingArray.forEach(input => {
            if (input.type == "text" || input.type == "select-one") {
                input.value = shippingArray[counter].value;
                counter++;
            }
        });
    } else {
        billingArray.forEach(input => {
            if (input.type == "text" || input.type == "select-one") {
                input.value = "";
            }
        })
    }
}

// Submits data to web2py for validation
function submitData(e) {
    e.preventDefault();

    // First make sure that if use shipping is checked, we are getting that data!
    copyShippingInput();

    const allForms = document.querySelectorAll('.order-forms');
    let allFormsData = {};

    // get data from each form
    allForms.forEach(form => {
        let formId = form.id;
        eachFormData = new FormData(form);
        let objectData = {};
        eachFormData.forEach((value, key) => {
            objectData[key] = value;
        });
        allFormsData[formId] = objectData
    });

    console.log(allFormsData)

    // send ajax request
    jQuery.ajax({
        url: 'checkout',
        type: 'POST',
        data: JSON.stringify(allFormsData),
        contentType: 'application/json',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        success: function (response) {
            response = JSON.parse(response)
            console.log(response)
            if (response.status === 'success') {
                window.location.href = response.redirect_url
            }
            else if (response.status === 'error') {
                // delete any existing error messages
                const allErrors = document.querySelectorAll(".error")
                allErrors.forEach(span => span.remove());
                // iterates through response.errors and adds error message for each one
                for (const formName in response.errors) {
                    const currentForm = document.querySelector(`#${formName}`);
                    Object.entries(response.errors[formName]).forEach(
                        ([inputName, errorMessage]) => {
                            const errorSpan = document.createElement("span");
                            errorSpan.classList.add("error", "text-danger");
                            errorSpan.textContent = errorMessage;
                            const currentInput = currentForm.querySelector(`[name="${inputName}"]`);
                            currentInput.parentElement.appendChild(errorSpan)
                        }
                    );
                }

                // UPDATE THE FORMKEY VALUES IN THE DOM
                if (response.new_keys) {
                    for (const formName in response.new_keys) {
                        const currentForm = document.querySelector(`#${formName}`);
                        if (currentForm) {
                            const formKeyInput = currentForm.querySelector('[name="_formkey"]');
                            if (formKeyInput) {
                                formKeyInput.value = response.new_keys[formName];
                            }
                        }
                    }
                }


            } // end if response error
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.error("AJAX Error:", textStatus, errorThrown, jqXHR.responseText);
            alert("An error occurred during submission.");
            // Consider displaying a general error message on the page if the AJAX call itself fails
        }
    });
    return false;
}


// EVENT LISTENERS
placeOrderBtn.addEventListener('click', submitData);
useShipping.addEventListener('change', copyShippingInput);
document.addEventListener("DOMContentLoaded", () => copyShippingInput());


