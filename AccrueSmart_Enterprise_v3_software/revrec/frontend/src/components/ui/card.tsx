export function Card(props:any){ return <div {...props} className={"bg-white rounded-xl border p-4 "+(props.className||"")}>{props.children}</div>; }
