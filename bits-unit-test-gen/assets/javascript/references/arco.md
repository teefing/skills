# Arco React Unit Test Reference

Use when source imports `@arco-design/web-react`. Keep this as a core-API reference, not a full component manual. API details are based on the official Arco React docs entry and `@arco-design/web-react` 2.66.15 type declarations.

## Test Strategy

- Load this reference together with `React.md` and usually `testing-library.md`.
- Import components from `@arco-design/web-react`; import icons from `@arco-design/web-react/icon` only when the tested source already depends on them.
- Do not add Arco CSS in unit tests unless the project already imports it in test setup. Assert behavior and visible content, not style implementation.
- Many overlays render into `document.body`: `Select`, `Cascader`, `TreeSelect`, `DatePicker`, `TimePicker`, `Tooltip`, `Popover`, `Popconfirm`, `Dropdown`, `Modal`, `Drawer`, `Image.Preview`, `Message`, `Notification`. Query `document.body` or pass `getPopupContainer` / `triggerProps.getPopupContainer` when the component under test allows it.
- Arco callbacks are often value-first, not native-event-first. Use the exact callback signatures below when asserting mock calls.
- For static feedback APIs (`Message`, `Notification`, `Modal.confirm`), prefer spying/mocking the static method when the source only triggers a toast/dialog; assert DOM only when the rendered overlay content itself matters.
- For form controls wrapped by `Form.Item`, assert submitted values through `onSubmit` or form instance methods. Use `triggerPropName="checked"` for `Checkbox` and `Switch`.
- For date/time components, Arco passes formatted strings plus `dayjs` instances. Tests can assert the string argument when dayjs identity/timezone is irrelevant.
- For virtualized components (`Table`, `List`, `Select`, `Transfer`, `Tree`) avoid expecting every item to exist in DOM unless virtualization is disabled.
- For transitions/async validation/popup visibility changes, use `await userEvent...`, `findBy*`, or `waitFor`.

## Shared API Shapes

| Shape | Core values |
|---|---|
| Sizes | Most inputs/buttons use `size: 'mini' | 'small' | 'default' | 'large'`; `Switch` uses `'small' | 'default'`; `Steps` uses `'default' | 'small'`. |
| Status | Inputs/selects/pickers often use `status: 'error' | 'warning'`; `Button.status` is `'warning' | 'danger' | 'success' | 'default'`; `Progress.status` is `'success' | 'error' | 'normal' | 'warning'`. |
| Popup triggers | `trigger: 'hover' | 'click' | 'focus' | 'contextMenu' | Array<...>`. |
| Popup positions | Usually `top`, `tl`, `tr`, `bottom`, `bl`, `br`, `left`, `lt`, `lb`, `right`, `rt`, `rb`; `DatePicker` / `TimePicker` commonly use the six top/bottom positions. |
| Controlled props | Use `value/defaultValue`, `checked/defaultChecked`, `visible`, `popupVisible/defaultPopupVisible`, `activeKey/defaultActiveKey`, `selectedKeys/defaultSelectedKeys`, `expandedKeys/defaultExpandedKeys`. |
| Select option | `string | number | { label: ReactNode | string; value: string | number; disabled?: boolean; extra?: any }`. |
| Cascader field names | `fieldNames` maps `label`, `value`, `isLeaf`, `disabled`, `children`. |
| Tree field names | `fieldNames` maps `key`, `title`, `isLeaf`, `disabled`, `children`, `selectable`, `disableCheckbox`, `checkable`. |
| Upload item | `{ uid, status?: 'init'|'uploading'|'done'|'error', originFile?, percent?, response?, url?, name? }`. |
| Transfer item | `{ key: string; value: string; disabled?: boolean }`. |

## Form

| API | Core details |
|---|---|
| `Form` props | `form`, `id`, `layout='horizontal'|'vertical'|'inline'`, `size`, `labelCol`, `wrapperCol`, `labelAlign`, `initialValues`, `validateTrigger`, `disabled`, `requiredSymbol`, `scrollToFirstError`, `validateMessages`. |
| `Form` callbacks | `onValuesChange(changedValues, allValues)`, `onChange(changedValues, allValues)` only for user changes, `onSubmit(values)`, `onSubmitFailed(errors)`. |
| `Form.Item` props | `field`, `label`, `tooltip`, `initialValue`, `rules`, `required`, `trigger='onChange'`, `triggerPropName='value'`, `getValueFromEvent`, `validateTrigger`, `noStyle`, `hidden`, `extra`, `help`, `validateStatus`, `hasFeedback`, `normalize`, `formatter`, `dependencies`, `shouldUpdate`. |
| `Form.Item` children | Can be React node or `(formData, form) => ReactNode`; render-prop items should be tested by changing dependent fields and asserting the rerendered output. |
| `Form.List` | `field`, `initialValue`, `rules`, `noStyle`; children receive `(fields, { add, remove, move })`. |
| Rules | `required`, `type`, `length`, `minLength`, `maxLength`, `min`, `max`, `match`, `validator(value, callback)`, `message`, `validateTrigger`, `validateLevel`. |
| Instance | `Form.useForm()` returns `[form]`; methods include `getFieldValue`, `getFieldsValue`, `getFieldError`, `setFieldValue`, `setFieldsValue`, `resetFields`, `clearFields`, `submit`, `validate`, `scrollToField`, `getFieldsState`. |
| Provider/hooks | `Form.Provider` has `onFormValuesChange(id, changed, { forms })`, `onFormSubmit(id, values, { forms })`; hooks include `useForm`, `useWatch`, `useFormContext`, `useFormState`. |

## Data Entry

| Component | Core props | Core callbacks / notes |
|---|---|---|
| `Input` | `value`, `defaultValue`, `placeholder`, `allowClear`, `disabled`, `readOnly`, `status`, `autoWidth`, `maxLength`, `showWordLimit`, `prefix`, `suffix`, `addBefore`, `addAfter`, `normalize`, `normalizeTrigger` | `onChange(value, e)`, `onClear()`, `onPressEnter(e)`. Accepts most native input props. |
| `Input.TextArea` | `value`, `defaultValue`, `placeholder`, `autoSize`, `allowClear`, `disabled`, `status`, `maxLength`, `showWordLimit`, `wordLimitPosition` | `onChange(value, e)`, `onClear()`, `onPressEnter(e)`. |
| `Input.Search` | All `Input` props plus `loading`, `searchButton` | `onSearch(value)`. User may trigger via search button or Enter depending on implementation. |
| `Input.Password` | All `Input` props plus `visibilityToggle`, `defaultVisibility`, `visibility` | `onVisibilityChange(visible)`. |
| `InputNumber` | `value`, `defaultValue`, `min`, `max`, `step`, `precision`, `mode='embed'|'button'`, `formatter`, `parser`, `hideControl`, `strictMode`, `prefix`, `suffix` | `onChange(value, reason)`, where reason is `'manual'|'increase'|'decrease'|'outOfRange'`; also `onFocus(e)`, `onBlur(e)`, `onKeyDown(e)`. |
| `InputTag` | `value`, `defaultValue`, `inputValue`, `labelInValue`, `allowClear`, `saveOnBlur`, `dragToSort`, `maxTagCount`, `tokenSeparators`, `validate`, `renderTag`, `prefix`, `suffix`, `addBefore`, `addAfter` | `onChange(value[], reason)`, reason is `'add'|'remove'|'clear'|'sort'`; `onRemove(value,index,e)`, `onInputChange(inputValue,e?)`, `onPressEnter(e)`, `onClear()`. |
| `VerificationCode` | `value`, `defaultValue`, `length`, `size`, `masked`, `disabled`, `readOnly`, `status='error'`, `validate`, `separator` | `onChange(value)`, `onFinish(value)`. Test by typing individual digits and waiting for final value. |
| `Mentions` | `value`, `defaultValue`, `options`, `prefix`, `split`, `alignTextarea`, `position`, `notFoundContent`, `filterOption`, `triggerProps`, `getPopupContainer` | `onChange(value)`, `onSearch(text, prefix)`, `onFocus(e)`, `onBlur(e)`. Extends `TextArea` props. |
| `AutoComplete` | `value`, `defaultValue`, `data`, `placeholder`, `allowClear`, `strict`, `loading`, `triggerElement`, `inputProps`, `filterOption`, `dropdownRender`, `virtualListProps` | `onSearch(value)`, `onSelect(value, option)`, `onChange(value, option?)`, `onPressEnter(e, activeOption?)`. |
| `Select` | `value`, `defaultValue`, `inputValue`, `mode='multiple'|'tags'`, `options`, `labelInValue`, `showSearch`, `filterOption`, `allowCreate`, `allowClear`, `popupVisible`, `defaultPopupVisible`, `notFoundContent`, `triggerElement`, `dropdownRender`, `virtualListProps` | `onChange(value, option)`, `onSelect(value, option)`, `onDeselect(value, option)`, `onClear(visible)`, `onSearch(value, reason)`, `onVisibleChange(visible)`, `onInputValueChange(value, reason)`. Reason is `'manual'|'optionChecked'|'optionListHide'|'tokenSeparator'`. |
| `Select.Option` / `OptGroup` | `Option.value`, `disabled`, `extra`, `children`; `OptGroup.label` / children | Prefer `options` prop in small tests unless source uses children. |
| `Cascader` | `value`, `defaultValue`, `options`, `fieldNames`, `mode='multiple'`, `showSearch`, `expandTrigger='click'|'hover'`, `changeOnSelect`, `checkedStrategy`, `loadMore`, `popupVisible`, `dropdownRender`, `dropdownColumnRender`, `renderOption`, `renderFormat` | `onChange(value, selectedOptions, extra)`, `onSearch(inputValue, reason)`, `onInputValueChange(inputValue, reason)`, `onVisibleChange(visible)`, `onClear(visible)`. |
| `TreeSelect` | `value`, `defaultValue`, `treeData`, `fieldNames`, `multiple`, `labelInValue`, `treeCheckable`, `treeCheckStrictly`, `treeCheckedStrategy`, `treeProps`, `popupVisible`, `filterTreeNode`, `loadMore`, `renderFormat` | `onChange(value, extra)`, `onSearch(inputValue)`, `onInputValueChange(value, reason)`, `onVisibleChange(visible)`, `onClear(visible)`. |
| `Checkbox` | `checked`, `defaultChecked`, `indeterminate`, `disabled`, `error`, `value`, `icon` | `onChange(checked, e)`. In forms, use `triggerPropName="checked"`. |
| `Checkbox.Group` | `value`, `defaultValue`, `options`, `disabled`, `direction`, `error` | `onChange(value[], e)`. |
| `Radio` | `checked`, `defaultChecked`, `disabled`, `value` | `onChange(checked, e)`. |
| `Radio.Group` | `value`, `defaultValue`, `options`, `disabled`, `name`, `type='radio'|'button'`, `direction`, `size`, `mode` | `onChange(value, e)`. |
| `Switch` | `checked`, `defaultChecked`, `disabled`, `loading`, `type='circle'|'round'|'line'`, `checkedText`, `uncheckedText`, `checkedIcon`, `uncheckedIcon` | `onChange(value, e)`. In forms, use `triggerPropName="checked"`. |
| `Slider` | `value`, `defaultValue`, `min`, `max`, `step`, `range`, `marks`, `onlyMarkValue`, `showInput`, `vertical`, `disabled`, `tooltipVisible`, `formatTooltip` | `onChange(value)`, `onAfterChange(value)`. Value is `number | number[]`. |
| `Rate` | `value`, `defaultValue`, `count`, `character`, `tooltips`, `allowHalf`, `allowClear`, `readonly`, `disabled`, `grading` | `onChange(value)`, `onHoverChange(value)`. |
| `DatePicker` family | `value`, `defaultValue`, `format`, `showTime`, `timepickerProps`, `disabledDate`, `disabledTime`, `allowClear`, `popupVisible`, `pickerValue`, `shortcuts`, `defaultPickerValue`, `utcOffset`, `timezone`; includes `WeekPicker`, `MonthPicker`, `YearPicker`, `QuarterPicker`, `RangePicker` | Single: `onChange(dateString, dayjs)`, `onSelect(dateString, dayjs)`, `onOk(dateString, dayjs)`. Range: `onChange(string[], dayjs[])`, `onSelect(string[], dayjs[], { type })`, `onOk(string[], dayjs[])`. |
| `TimePicker` family | `value`, `defaultValue`, `format`, `use12Hours`, `step`, `disableConfirm`, `disabledHours`, `disabledMinutes`, `disabledSeconds`, `showNowBtn`, `popupVisible`; includes `RangePicker` | Single: `onChange(valueString, dayjs)`, `onSelect(valueString, dayjs)`. Range: `onChange(string[], dayjs[])`, `onSelect(string[], dayjs[])`. |
| `Upload` | `fileList`, `defaultFileList`, `accept`, `customRequest`, `listType='text'|'picture-list'|'picture-card'`, `showUploadList`, `autoUpload`, `action`, `method`, `limit`, `disabled`, `drag`, `multiple`, `beforeUpload`, `renderUploadItem`, `renderUploadList` | `onChange(fileList,file)`, `onPreview(file)`, `onRemove(file,fileList)`, `onProgress(file,e)`, `onReupload(file)`, `onExceedLimit(files,fileList)`, `onDrop(e)`. Ref methods: `submit(file?)`, `abort(file)`, `reupload(file)`. |
| `Transfer` | `dataSource`, `targetKeys`, `defaultTargetKeys`, `selectedKeys`, `defaultSelectedKeys`, `titleTexts`, `operationTexts`, `disabled`, `oneWay`, `simple`, `draggable`, `showSearch`, `pagination`, `render`, `filterOption`, custom-list children | `onChange(targetKeys, direction, moveKeys)`, `onSelectChange(leftKeys,rightKeys)`, `onSearch(value,type)`, `onResetData()`, drag callbacks. |

## Feedback And Overlay

| Component | Core API |
|---|---|
| `Modal` | Props: `visible`, `title`, `footer`, `okText`, `cancelText`, `okButtonProps`, `cancelButtonProps`, `closable`, `maskClosable`, `confirmLoading`, `mountOnEnter`, `unmountOnExit`, `simple`, `hideCancel`, `focusLock`, `autoFocus`, `modalRender`, `getPopupContainer`, `getChildrenPopupContainer`, `onOk(e)`, `onCancel()`, `afterOpen()`, `afterClose()`. Static: `Modal.confirm/info/success/warning/error(config)`, `Modal.config`, `Modal.destroyAll`, `Modal.useModal`. Static call returns `{ update, close }`. |
| `Drawer` | `visible`, `title`, `footer`, `placement='top'|'right'|'bottom'|'left'`, `width`, `height`, `mask`, `closable`, `maskClosable`, `confirmLoading`, `okText`, `cancelText`, `mountOnEnter`, `unmountOnExit`, `focusLock`, `getPopupContainer`, `getChildrenPopupContainer`, `onOk(e)`, `onCancel(e)`, `afterOpen()`, `afterClose()`. |
| `Message` | Static: `Message.success/info/warning/error/loading/normal(configOrString)`, `Message.config(options)`, `Message.clear()`, `Message.useMessage()`. Config: `content`, `duration`, `id`, `position='top'|'bottom'`, `closable`, `showIcon`, `icon`, `onClose`. Static call returns a close function-like object. |
| `Notification` | Static: `Notification.success/info/warning/error/normal(config)`, `Notification.config(options)`, `Notification.remove(id)`, `Notification.clear()`, `Notification.useNotification()`. Config: `title`, `content`, `duration`, `id`, `position='topLeft'|'topRight'|'bottomLeft'|'bottomRight'`, `btn`, `closable`, `showIcon`, `icon`, `onClose`. |
| `Tooltip` | `content`, `trigger`, `position`, `popupVisible`, `defaultPopupVisible`, `disabled`, `color`, `mini`, `blurToHide`, `popupHoverStay`, `unmountOnExit`, `triggerProps`, `getPopupContainer`, `onVisibleChange(visible)`. |
| `Popover` | Extends Tooltip without `mini`; adds `title` and uses `content`. |
| `Popconfirm` | `title`, `content`, `okText`, `cancelText`, `okType`, `okButtonProps`, `cancelButtonProps`, `popupVisible`, `defaultPopupVisible`, `trigger`, `position`, `icon`, `autoFocus`, `focusLock`, `onOk(e)`, `onCancel(e)`, `onVisibleChange(visible)`. |
| `Dropdown` | `droplist`, `trigger`, `position`, `disabled`, `popupVisible`, `defaultPopupVisible`, `triggerProps`, `getPopupContainer`, `onVisibleChange(visible)`. |
| `Dropdown.Button` | Dropdown props plus `size`, `type`, `buttonProps`, `icon`, `buttonsRender(buttons)`, `onClick(e)`. |

## Navigation And Layout

| Component | Core API |
|---|---|
| `Button` / `Button.Group` | `type='default'|'primary'|'secondary'|'dashed'|'text'|'outline'`, `status`, `size`, `shape='circle'|'round'|'square'`, `htmlType='button'|'submit'|'reset'`, `href`, `target`, `disabled`, `loading`, `loadingFixedWidth`, `icon`, `iconOnly`, `long`, `onClick(e)`. |
| `Link` | Anchor props plus `icon`, `status='error'|'success'|'warning'`, `disabled`, `hoverable`. |
| `Menu` | `theme`, `mode='vertical'|'horizontal'|'pop'|'popButton'`, `collapse`, `accordion`, `selectable`, `selectedKeys`, `defaultSelectedKeys`, `openKeys`, `defaultOpenKeys`, `autoOpen`, `hasCollapseButton`, `triggerProps`, `tooltipProps`, `onClickMenuItem(key,event,keyPath)`, `onClickSubMenu(key,openKeys,keyPath)`, `onCollapseChange(collapse)`. Subcomponents: `Menu.Item key`, `Menu.SubMenu key/title`, `Menu.ItemGroup title`. |
| `Tabs` | `activeTab`, `defaultActiveTab`, `type='line'|'card'|'card-gutter'|'text'|'rounded'|'capsule'`, `tabPosition`, `editable`, `showAddButton`, `destroyOnHide`, `lazyload`, `overflow`, `extra`, `icons`, `onChange(key)`, `onClickTab(key)`, `onAddTab()`, `onDeleteTab(key)`. `Tabs.TabPane`: `title`, `disabled`, `closable`, `destroyOnHide`. |
| `Pagination` | `current`, `defaultCurrent`, `pageSize`, `defaultPageSize`, `total`, `disabled`, `hideOnSinglePage`, `size`, `showTotal`, `sizeCanChange`, `sizeOptions`, `bufferSize`, `simple`, `showJumper`, `showMore`, `itemRender`, `onChange(page,pageSize)`, `onPageSizeChange(size,current)`. |
| `Breadcrumb` | `separator`, `routes`, `maxCount`, `itemRender(route,routes,paths)`. `Breadcrumb.Item`: `droplist`, `dropdownProps`, `href`, `tagName`, `onClick(e)`. |
| `Anchor` | `animation`, `direction`, `scrollContainer`, `boundary`, `hash`, `affix`, `offsetTop`, `offsetBottom`, `targetOffset`, `lineless`, `onChange(newLink,oldLink)`, `onSelect(newLink,oldLink)`. `Anchor.Link`: `href`, `title`. |
| `Layout` | `Layout.hasSider`; `Header`, `Footer`, `Content`; `Sider`: `theme`, `collapsed`, `defaultCollapsed`, `collapsible`, `collapsedWidth`, `trigger`, `width`, `breakpoint`, `resizeDirections`, `resizeBoxProps`, `onCollapse(collapse,type)`, `onBreakpoint(broken)`. |
| `Grid` / `Row` / `Col` | `Row.gutter`, `align`, `justify`; `Col.span`, `offset`, `order`, `push`, `pull`, `xs`-`xxxl`, `flex`; `Grid.cols`, `rowGap`, `colGap`, `collapsed`, `collapsedRows`; `GridItem.span`, `offset`, `suffix`. |
| `Space` | `direction='vertical'|'horizontal'`, `size='mini'|'small'|'medium'|'large'|number|array`, `align`, `wrap`, `split`. |
| `Divider` | `type='horizontal'|'vertical'`, `orientation='left'|'right'|'center'`. |
| `Affix` | `offsetTop`, `offsetBottom`, `target`, `targetContainer`, `affixClassName`, `affixStyle`, `onChange(affixed)`. |
| `BackTop` | `visibleHeight`, `target`, `duration`, `easing`, `onClick()`. |

## Data Display

| Component | Core API |
|---|---|
| `Table` | `columns`, `data`, `rowKey`, `pagination`, `loading`, `border`, `hover`, `stripe`, `size`, `rowSelection`, `expandedRowRender`, `expandedRowKeys`, `defaultExpandedRowKeys`, `scroll`, `virtualized`, `noDataElement`, `placeholder`, `footer`, `summary`, `onChange(pagination, sorter, filters, extra)`, `onRow(record,index)`, `onHeaderRow(columns,index)`, `onExpand(record,expanded)`, `onExpandedRowsChange(keys)`. |
| `Table` column | `title`, `dataIndex`, `key`, `render(col,record,index)`, `width`, `align`, `ellipsis`, `sorter`, `sortOrder`, `defaultSortOrder`, `filters`, `filteredValue`, `defaultFilters`, `onFilter(value,row)`, `filterDropdown`, `fixed`, `onCell(record,index)`, `onHeaderCell(column,index)`, nested `children`. |
| `Table.rowSelection` | `type='checkbox'|'radio'`, `selectedRowKeys`, `checkAll`, `checkStrictly`, `checkboxProps(record)`, `renderCell(originNode,checked,record)`, `preserveSelectedRowKeys`, `onChange(keys,rows)`, `onSelect(selected,record,rows)`, `onSelectAll(selected,rows)`. |
| `Tree` | `treeData`, `fieldNames`, `selectedKeys`, `defaultSelectedKeys`, `checkedKeys`, `defaultCheckedKeys`, `halfCheckedKeys`, `expandedKeys`, `defaultExpandedKeys`, `checkable`, `checkStrictly`, `checkedStrategy='all'|'parent'|'child'`, `multiple`, `selectable`, `loadMore`, `renderTitle`, `renderExtra`, `actionOnClick`, `draggable`, `allowDrop`, `onSelect(keys,extra)`, `onCheck(keys,extra)`, `onExpand(keys,extra)`, `onDrop(info)`. |
| `List` | `dataSource`, `render(item,index)`, `children`, `size`, `header`, `footer`, `pagination`, `bordered`, `split`, `grid`, `loading`, `hoverable`, `onReachBottom(page)`, `onListScroll(elem)`, `scrollLoading`, `noDataElement`, `virtualListProps`. `List.Item`: `actions`, `extra`, `actionLayout`; `List.Item.Meta`: `title`, `avatar`, `description`. |
| `Card` | `bordered`, `loading`, `hoverable`, `size`, `title`, `extra`, `cover`, `actions`, `headerStyle`, `bodyStyle`. `Card.Meta`: `avatar`, `title`, `description`, `actionList`. `Card.Grid`: `hoverable`. |
| `Descriptions` | `data: { key?, label?, value?, span? }[]`, `column`, `title`, `colon`, `border`, `layout`, `size`, `tableLayout`, `labelStyle`, `valueStyle`. |
| `Collapse` | `activeKey`, `defaultActiveKey`, `accordion`, `expandIcon`, `expandIconPosition`, `bordered`, `lazyload`, `destroyOnHide`, `triggerRegion`, `onChange(key,keys,e)`. `Collapse.Item`: `name`, `header`, `disabled`, `extra`, `showExpandIcon`, `contentStyle`. |
| `Calendar` | `value`, `defaultValue`, `pageShowDate`, `defaultPageShowDate`, `mode`, `defaultMode`, `modes`, `panel`, `allowSelect`, `isWeek`, `dayStartOfWeek`, `disabledDate`, `dateRender`, `monthRender`, `dateInnerContent`, `headerRender`, `onChange(dayjs)`, `onPanelChange(dayjs)`. |
| `Carousel` | `currentIndex`, `autoPlay`, `moveSpeed`, `animation='slide'|'card'|'fade'`, `trigger='click'|'hover'`, `direction`, `showArrow`, `indicatorType`, `indicatorPosition`, `icons`, `onChange(index,prevIndex,isManual)`, `carousel` ref with `goto({ index, isNegative?, isManual?, resetAutoPlayInterval? })`. |
| `Image` | `src`, `width`, `height`, `title`, `description`, `actions`, `footerPosition`, `simple`, `loader`, `error`, `preview`, `previewProps`, `lazyload`, `onLoad(e)`, `onError(e)`. `Image.Preview`: `src`, `visible`, `defaultVisible`, `maskClosable`, `closable`, `actions`, `actionsLayout`, `onVisibleChange(visible,prev)`. `PreviewGroup`: `srcList`, `current`, `defaultCurrent`, `infinite`, `onChange(index)`. |
| `Avatar` | `shape`, `size`, `autoFixFontSize`, `triggerIcon`, `triggerType`, `onClick(e)`. `Avatar.Group`: `shape`, `size`, `maxCount`, `maxStyle`, `maxPopoverTriggerProps`, `zIndexAscend`. |
| `Badge` | `count`, `text`, `dot`, `maxCount`, `offset`, `color`, `status`, `dotStyle`, `dotClassName`. |
| `Tag` | `color`, `bordered`, `size`, `visible`, `closable`, `checkable`, `checked`, `defaultChecked`, `icon`, `closeIcon`, `onClose(e)`, `onCheck(checked)`. |
| `Typography` | `Text`, `Title`, `Paragraph`, `Ellipsis`; common props: `type`, `bold`, `disabled`, `mark`, `underline`, `delete`, `code`, `copyable`, `editable`, `ellipsis`. `Title.heading`; `Paragraph.blockquote` / `spacing`. `copyable.onCopy(text,e)`, `editable.onChange(text)`, `editable.onEnd(text)`. |
| `Statistic` | `title`, `value`, `precision`, `groupSeparator`, `prefix`, `suffix`, `extra`, `countUp`, `countFrom`, `countDuration`, `format`, `renderFormat(value,formatted)`, `loading`. `Statistic.Countdown`: `value`, `format`, `start`, `now`, `renderFormat(diff,formatted)`, `onFinish()`. |
| `Progress` | Required `percent`; `type='line'|'circle'`, `steps`, `animation`, `status`, `color`, `trailColor`, `showText`, `formatText(percent)`, `strokeWidth`, `width`, `size`, `buffer`, `bufferColor`. |
| `Steps` | `current`, `status`, `type`, `size`, `direction`, `labelPlacement`, `customDot`, `lineless`, `onChange(current,id)`. `Steps.Step`: `title`, `description`, `icon`, `status`, `disabled`, `id`, `onClick(index,id,e)`. |
| `Timeline` | `reverse`, `direction`, `mode`, `pending`, `pendingDot`, `labelPosition`. `Timeline.Item`: `dotColor`, `dotType`, `dot`, `lineType`, `lineColor`, `label`, `position`, `children`. |
| `Alert` | `type='info'|'success'|'warning'|'error'`, `title`, `content`, `action`, `closable`, `closeElement`, `showIcon`, `icon`, `banner`, `onClose(e)`, `afterClose()`. |
| `Spin` | `loading`, `size`, `icon`, `element`, `tip`, `delay`, `dot`, `block`, `children`. |
| `Empty` | `description`, `icon`, `imgSrc`. |
| `Result` | `status='success'|'error'|'info'|'warning'|'404'|'403'|'500'|null`, `title`, `subTitle`, `icon`, `extra`. |
| `Skeleton` | `loading`, `animation`, `image`, `text`; image props include `shape`, `size`, `position`; text props include `rows`, `width`. |
