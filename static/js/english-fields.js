/**
 * English Fields JavaScript
 * Converts Arabic numerals (٠١٢٣٤٥٦٧٨٩) to English numerals (0123456789)
 * in English/LTR fields
 */

(function() {
    'use strict';

    // Arabic to English numeral mapping
    const arabicToEnglish = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    };

    // English to Arabic numeral mapping (for reverse conversion if needed)
    const englishToArabic = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
        '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
    };

    /**
     * Convert Arabic numerals to English numerals in a string
     */
    function convertArabicToEnglish(text) {
        if (!text) return text;
        let result = text;
        for (const [arabic, english] of Object.entries(arabicToEnglish)) {
            result = result.replace(new RegExp(arabic, 'g'), english);
        }
        return result;
    }

    /**
     * Check if an input field should use English numerals
     */
    function isEnglishField(input) {
        // Check by class
        if (input.classList.contains('english-field') || 
            input.classList.contains('ltr-field') ||
            input.classList.contains('english-only')) {
            return true;
        }

        // Check by input type
        const englishTypes = ['email', 'password', 'tel', 'url'];
        if (englishTypes.includes(input.type)) {
            return true;
        }

        // Check by field name
        const englishFieldNames = [
            'username', 'email', 'password', 'phone', 'mobile',
            'plate_no_en', 'fleet_no', 'code', 'serial', 'vin',
            'url', 'website'
        ];
        const fieldName = input.name || input.id || '';
        for (const name of englishFieldNames) {
            if (fieldName.toLowerCase().includes(name)) {
                return true;
            }
        }

        // Check by ID
        const fieldId = input.id || '';
        for (const name of englishFieldNames) {
            if (fieldId.toLowerCase().includes(name)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Handle input event to convert Arabic numerals to English
     */
    function handleInput(event) {
        const input = event.target;
        
        if (!isEnglishField(input)) {
            return;
        }

        const originalValue = input.value;
        const convertedValue = convertArabicToEnglish(originalValue);

        if (originalValue !== convertedValue) {
            // Get cursor position
            const cursorPosition = input.selectionStart;
            
            // Update value
            input.value = convertedValue;
            
            // Restore cursor position (adjust for any character changes)
            // Since we're only replacing single characters, position should be same
            input.setSelectionRange(cursorPosition, cursorPosition);
        }
    }

    /**
     * Handle paste event to convert Arabic numerals in pasted text
     */
    function handlePaste(event) {
        const input = event.target;
        
        if (!isEnglishField(input)) {
            return;
        }

        // Get pasted text
        const pastedText = (event.clipboardData || window.clipboardData).getData('text');
        const convertedText = convertArabicToEnglish(pastedText);

        if (pastedText !== convertedText) {
            // Prevent default paste
            event.preventDefault();
            
            // Get current selection
            const start = input.selectionStart;
            const end = input.selectionEnd;
            const currentValue = input.value;
            
            // Insert converted text
            const newValue = currentValue.substring(0, start) + convertedText + currentValue.substring(end);
            input.value = newValue;
            
            // Set cursor position after pasted text
            const newPosition = start + convertedText.length;
            input.setSelectionRange(newPosition, newPosition);
        }
    }

    /**
     * Initialize English fields conversion
     */
    function initializeEnglishFields() {
        // Find all English fields
        const englishFields = document.querySelectorAll(
            'input.english-field, ' +
            'input.ltr-field, ' +
            'input[type="email"], ' +
            'input[type="password"], ' +
            'input[type="tel"], ' +
            'input[type="url"], ' +
            'input[name*="username"], ' +
            'input[name*="email"], ' +
            'input[name*="password"], ' +
            'input[name*="phone"], ' +
            'input[name*="mobile"], ' +
            'input[name*="plate_no_en"], ' +
            'input[name*="fleet_no"], ' +
            'input[name*="code"], ' +
            'input[name*="serial"], ' +
            'input[name*="vin"]'
        );

        // Add event listeners
        englishFields.forEach(function(field) {
            // Add lang attribute to help browsers use English keyboard
            field.setAttribute('lang', 'en');
            field.setAttribute('inputmode', 'latin');
            
            // Remove existing listeners to avoid duplicates
            field.removeEventListener('input', handleInput);
            field.removeEventListener('paste', handlePaste);
            
            // Add event listeners
            field.addEventListener('input', handleInput, false);
            field.addEventListener('paste', handlePaste, false);
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeEnglishFields);
    } else {
        initializeEnglishFields();
    }

    // Re-initialize for dynamically added fields (e.g., forms added via AJAX)
    // Use MutationObserver to watch for new inputs
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.tagName === 'INPUT' && isEnglishField(node)) {
                            node.setAttribute('lang', 'en');
                            node.setAttribute('inputmode', 'latin');
                            node.addEventListener('input', handleInput, false);
                            node.addEventListener('paste', handlePaste, false);
                        } else if (node.querySelectorAll) {
                            // Check for inputs within added nodes
                            const inputs = node.querySelectorAll('input');
                            inputs.forEach(function(input) {
                                if (isEnglishField(input)) {
                                    input.setAttribute('lang', 'en');
                                    input.setAttribute('inputmode', 'latin');
                                    input.addEventListener('input', handleInput, false);
                                    input.addEventListener('paste', handlePaste, false);
                                }
                            });
                        }
                    }
                });
            }
        });
    });

    // Start observing
    if (document.body) {
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    } else {
        document.addEventListener('DOMContentLoaded', function() {
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
    }

})();

