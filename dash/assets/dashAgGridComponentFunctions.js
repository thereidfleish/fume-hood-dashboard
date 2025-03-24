var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.Button = function (props) {
    const { setData, data } = props;

    function onClick() {
        setData(data); 
        console.log("Button clicked in row:", data);  
    }

    return React.createElement(
        'button',
        {
            onClick: onClick,
            className: props.className || "test-button"
        },
        props.value || "run"
    );
};
