import { Popover, Button } from 'antd'

const CurrentUser = () => {
    return (
        <>
            <Popover
                placement='bottomRight'
                trigger={['click']}
                overlayInnerStyle={{ padding: 0 }}
                overlayStyle={{ zIndex: 9999 }}
            >
                Test
            </Popover >
        </>
    )
}

export default CurrentUser