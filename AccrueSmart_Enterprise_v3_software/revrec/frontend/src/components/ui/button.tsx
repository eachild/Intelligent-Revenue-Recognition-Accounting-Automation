export function Button(props:any){ return <button {...props} className={"px-3 py-2 rounded border "+(props.className||"")}>{props.children}</button>; }
