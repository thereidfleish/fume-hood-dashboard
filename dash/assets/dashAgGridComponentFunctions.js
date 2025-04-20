// import isPropValid from '@emotion/is-prop-valid';

// function shouldForwardProp(propName, target) {
//     if (typeof target === "string") {
//         return isPropValid(propName);
//     }
//     return true;
// }


console.log("dashAgGridComponentFunctions.js loaded");
window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};
var dagcomponentfuncs = window.dashAgGridComponentFunctions;
console.log("dagcomponentfuncs object:", dagcomponentfuncs);
console.log("Custom renderer registered:", dagcomponentfuncs.button);



dagcomponentfuncs.button = function (props) {
    console.log("=== Button Component ===");
    console.log("All props:", JSON.stringify(props, null, 2));
    console.log("Data type:", typeof props.data);
    console.log("Value type:", typeof props.value);
    console.log("Raw data:", props.data);
    console.log("Raw value:", props.value);

    const { data, setData, value, className } = props;
    let buttonClass = "test-button"; // Default class

    // Check for test results immediately when component renders
    if (data && typeof data === 'string') {
        try {
            const results = JSON.parse(data);
            console.log("Parsed results:", results);
            console.log("Looking for match with row id:", value);
            
            // Try different ways to match the ID
            const testResult = results.find(r => {
                console.log("Comparing:", r.id, "with", value);
                return r.id === value;
            });
            console.log("Found test result:", testResult);
            
            if (testResult) {
                console.log("Test message:", testResult.message);
                buttonClass = testResult.message === "success" ? 
                    "test-button test-succeeds" : 
                    "test-button test-fails";
                console.log("Setting button class to:", buttonClass);
            }
        } catch (e) {
            console.error("Error parsing test results:", e);
            buttonClass = "test-button test-fails";
        }
    }

    return React.createElement(
        "button",
        {
            className: buttonClass,
            style: { 
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                transform: 'translate(5px, 10px)',
                border: 'none',
                padding: '10px 10px',
                borderRadius: '20px',
                cursor: 'pointer'
            }
        },
        "Test"
    );
};
