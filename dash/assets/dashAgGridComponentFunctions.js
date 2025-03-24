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
    console.log("Button props:", props);

    const { data, setData, value, className } = props;

    function onClick(event) {
        if (data) {
            setData(data);
            console.log("Button clicked in row:", data);
            event.target.classList.add("test-succeeds");
            event.target.classList.remove("test-fails");
        } else {
            console.log("No data returned.");
            event.target.classList.add("test-fails");
            event.target.classList.remove("test-succeeds");
        }
    }

    return React.createElement(
        "button",
        {
            onClick: onClick,
            className: className || "test-button"
        },
        value 
    );
};
